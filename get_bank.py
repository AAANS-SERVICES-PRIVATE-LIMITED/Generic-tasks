"""
get_bank.py — Entry point for bank statement extraction.

Pipeline:
  1. Convert PDF page-1 to image (or use image directly)
  2. Run Tesseract OCR on the image for bank detection
  3. Run MinerU on the full file for structured markdown output
  4. Detect bank using a multi-source scoring system (name patterns + IFSC)
  5. Dynamically load the bank-specific template and call extract()
  6. Return a structured dict {bank, confidence, data}

Configuration (via environment variables):
  TESSERACT_CMD   — path to tesseract.exe  (default: system PATH)
  MINERU_TIMEOUT  — seconds before MinerU is killed  (default: 180)
  OCR_DPI         — DPI for PDF→image conversion  (default: 300)
"""

import os
import re
import subprocess
import sys
import tempfile
import json
import logging
import importlib
import importlib.util
import shutil
from pathlib import Path

from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# =========================
# LOGGING SETUP
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bank_extractor")

# =========================
# CONFIG  (no hardcoded paths)
# =========================
TEMPLATE_PATH = Path(__file__).parent / "templates"

_tesseract_cmd = os.environ.get("TESSERACT_CMD", "")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd
else:
    # Windows default install location as a fallback (not hardcoded to one user)
    _win_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.isfile(_win_default):
        pytesseract.pytesseract.tesseract_cmd = _win_default

MINERU_TIMEOUT: int = int(os.environ.get("MINERU_TIMEOUT", "180"))
OCR_DPI: int = int(os.environ.get("OCR_DPI", "300"))


# =========================
# BANK DETECTION PATTERNS  (pre-compiled once at import time)
# =========================
_RAW_BANK_PATTERNS = {
    # Put longer/more specific patterns first to avoid substring matches
    # Handle OCR variations (e.g., Arcici, IcicI)
    r"[ai]cici\s*bank|[ai]cici|icici\s*bank|icici": "icici",
    r"\bhdfc\s*bank|\bhdfc": "hdfc",
    r"\bkotak\s*(?:mahindra\s*)?bank|\bkotak": "kotak",
    r"\bidfc\s*first\s*bank|\bidfc": "idfc",
    r"\bfederal\s*bank|\bfederal": "federal",
    r"\bindusind\s*bank|\bindusind": "indusind",
    r"\byes\s*bank": "yes",
    r"\bidbi\s*bank|\bidbi": "idbi",
    r"\bstate\s*bank\s*of\s*india|\bs\s*b\s*i|sbi": "sbi",
    r"\bbank\s*of\s*baroda|\bb\s*o\s*b|bob": "bob",
    r"\bpunjab\s*national\s*bank|\bp\s*n\s*b|pnb": "pnb",
    r"\bcanara\s*bank|\bcanara": "canara",
    r"\bunion\s*bank\s*of\s*india|\bu\s*b\s*i|ubi": "ubi",
    r"\bcentral\s*bank\s*of\s*india|\bc\s*b\s*i|cbi": "cbi",
    r"\bbank\s*of\s*india|\bb\s*o\s*i|boi": "boi",
    r"\bindian\s*overseas\s*bank|\bi\s*o\s*b|iob": "iob",
    r"\bbank\s*of\s*maharashtra|\bb\s*o\s*m|bom|maharashtra\s*bank": "bom",
    r"\bindian\s*bank": "indian",
    r"\buco\s*bank|\bu\s*c\s*o": "uco",
    r"\bpunjab\s*(?:&\s*|and\s*)?sind\s*bank|\bp\s*s\s*b|psb": "psb",
    r"\baxis\s*bank|\baxis": "axis",
    r"\brbl\s*bank|\brbl": "rbl",
    r"\bj\s*&\s*k\s*bank|\bjammu\s*and\s*kashmir\s*bank": "jk",
    r"\bkarnataka\s*bank": "karnataka",
    r"\bsouth\s*indian\s*bank": "south_indian",
    r"\bcity\s*union\s*bank": "city_union",
    r"\btamilnad\s*mercantile\s*bank|\btmb": "tmb",
    r"\bdcb\s*bank|\bdcb": "dcb",
    r"\bbandhan\s*bank|\bbandhan": "bandhan",
    r"\bairtel": "airtel",
}

# Compile all patterns once
BANK_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), bank)
    for pattern, bank in _RAW_BANK_PATTERNS.items()
]

# IFSC prefix → bank
IFSC_BANK_MAP: dict[str, str] = {
    "SBIN": "sbi", "BARB": "bob", "PUNB": "pnb", "CNRB": "canara",
    "UTBI": "ubi", "CBIN": "cbi", "BKID": "boi", "IOBA": "iob",
    "MAHB": "bom", "IDIB": "indian", "UCBA": "uco", "PSIB": "psb",
    "UTIB": "axis", "HDFC": "hdfc", "ICIC": "icici", "KKBK": "kotak",
    "YESB": "yes", "IBKL": "idbi", "INDB": "indusind", "IDFB": "idfc",
    "FDRL": "federal", "RATN": "rbl", "JAKA": "jk", "KARB": "karnataka",
    "SIBL": "south_indian", "CIUB": "city_union", "TMBL": "tmb",
    "DCBL": "dcb", "BDBL": "bandhan",
}


# =========================
# TEXT NORMALISATION
# =========================
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================
# BANK DETECTION
# =========================
def detect_bank_from_text(text: str) -> tuple[str | None, str | None]:
    """
    Detect bank from a single text source using name patterns and IFSC codes.

    Returns (bank_from_name, bank_from_ifsc). Either may be None.
    """
    if not text:
        return None, None

    normalized = normalize(text)

    # --- Name pattern matching (pick the longest match = most specific) ---
    bank_from_name: str | None = None
    best_score = 0
    for compiled_pattern, bank in BANK_PATTERNS:
        match = compiled_pattern.search(normalized)
        if match:
            score = len(match.group(0))
            if score > best_score:
                best_score = score
                bank_from_name = bank

    # --- IFSC code matching ---
    bank_from_ifsc: str | None = None
    text_upper = text.upper()
    ifsc_matches = re.findall(r"\b([A-Z]{4}[0O][A-Z0-9]{6,7})\b", text_upper)
    for ifsc in ifsc_matches:
        bank_code = ifsc[:4]
        if bank_code in IFSC_BANK_MAP:
            bank_from_ifsc = IFSC_BANK_MAP[bank_code]
            break

    return bank_from_name, bank_from_ifsc


def detect_bank(ocr_text: str, mineru_text: str | None = None) -> tuple[str | None, int]:
    """
    Multi-source bank detection with a confidence score.

    Scoring:
      • OCR name: 1 point
      • OCR IFSC: 3 points (higher priority than name)
      • MinerU name: 2 points
      • MinerU IFSC: 4 points (highest priority)
      • The bank with the highest score wins.
      • Max score: 10 (1 OCR name + 3 OCR IFSC + 2 MinerU name + 4 MinerU IFSC)
    """
    scores: dict[str, int] = {}

    # OCR sources
    ocr_name, ocr_ifsc = detect_bank_from_text(ocr_text)
    if ocr_name:
        scores[ocr_name] = scores.get(ocr_name, 0) + 1
    if ocr_ifsc:
        scores[ocr_ifsc] = scores.get(ocr_ifsc, 0) + 3  # IFSC gets higher priority

    # MinerU sources
    if mineru_text:
        mn_name, mn_ifsc = detect_bank_from_text(mineru_text)
        if mn_name:
            scores[mn_name] = scores.get(mn_name, 0) + 2
        if mn_ifsc:
            scores[mn_ifsc] = scores.get(mn_ifsc, 0) + 4  # MinerU IFSC gets highest priority

    if not scores:
        return None, 0

    best_bank = max(scores, key=lambda b: scores[b])
    best_score = scores[best_bank]
    return best_bank, best_score


# =========================
# OCR  (unified helper)
# =========================
def run_ocr(image: Image.Image) -> str:
    """Run Tesseract OCR on a PIL Image and return the text."""
    try:
        return pytesseract.image_to_string(image)
    except Exception as exc:
        logger.error("Tesseract OCR failed: %s", exc)
        return ""


def get_first_page_image(pdf_path: str) -> Image.Image | None:
    """Convert the first page of a PDF to a PIL Image at OCR_DPI resolution."""
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=OCR_DPI)
        return images[0] if images else None
    except Exception as exc:
        logger.error("PDF to image conversion failed for '%s': %s", pdf_path, exc)
        return None


# =========================
# MINERU
# =========================
def run_mineru(path: str) -> str | None:
    """
    Run MinerU on *path* and return the extracted markdown text, or None on failure.

    Uses a unique temp directory per call to avoid race conditions.
    Kills MinerU if it exceeds MINERU_TIMEOUT seconds.
    """
    tmp = tempfile.mkdtemp(prefix="mineru_")
    try:
        cmd = ["mineru", "-p", path, "-o", tmp, "-b", "pipeline"]
        env = os.environ.copy()
        env["MINERU_DISABLE_VLM"] = "true"
        env["CUDA_VISIBLE_DEVICES"] = ""

        logger.info("Running MinerU on '%s' (timeout=%ss)", path, MINERU_TIMEOUT)
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=MINERU_TIMEOUT,
        )

        if res.returncode != 0:
            logger.warning("MinerU exited with code %d: %s", res.returncode, res.stderr[:500])
            return None

        # Pick the largest .md file produced (main content)
        md_files = [
            os.path.join(r, f)
            for r, _, files in os.walk(tmp)
            for f in files
            if f.endswith(".md")
        ]
        if not md_files:
            logger.warning("MinerU produced no .md files for '%s'", path)
            return None

        largest = max(md_files, key=os.path.getsize)
        with open(largest, "r", encoding="utf-8") as fp:
            return fp.read()

    except subprocess.TimeoutExpired:
        logger.error("MinerU timed out after %ss for '%s'", MINERU_TIMEOUT, path)
        return None
    except Exception as exc:
        logger.error("MinerU failed unexpectedly for '%s': %s", path, exc)
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# =========================
# TEMPLATE LOADER
# =========================
# Ensure the tools_test directory is on sys.path so `templates` is importable as a package
_TOOLS_TEST_DIR = str(Path(__file__).parent)
if _TOOLS_TEST_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_TEST_DIR)


def load_template(bank_name: str):
    """
    Dynamically import templates/<bank_name>.py via the package system.

    Using importlib.import_module ensures relative imports (from .base import ...)
    inside each template module work correctly.

    Returns None if the template file does not exist or fails to import.
    """
    file_path = TEMPLATE_PATH / f"{bank_name}.py"
    if not file_path.exists():
        logger.warning("No template found for bank '%s' (expected: %s)", bank_name, file_path)
        return None

    module_name = f"templates.{bank_name}"
    try:
        # importlib.import_module handles caching; re-import if already loaded
        if module_name in sys.modules:
            return sys.modules[module_name]
        return importlib.import_module(module_name)
    except Exception as exc:
        logger.error("Failed to load template for '%s': %s", bank_name, exc)
        return None


# =========================
# INPUT VALIDATION
# =========================
_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}


def validate_input_path(path: str) -> str:
    """
    Validate that *path* points to an existing, supported file.

    Raises ValueError with a descriptive message on invalid input.
    Returns the resolved absolute path string.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise ValueError(f"Input file does not exist: {p}")
    if not p.is_file():
        raise ValueError(f"Input path is not a file: {p}")
    if p.suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{p.suffix}'. "
            f"Allowed: {sorted(_ALLOWED_EXTENSIONS)}"
        )
    return str(p)


# =========================
# MAIN PIPELINE
# =========================
def process(path: str) -> dict:
    """
    Full extraction pipeline for a single bank statement file.

    Args:
        path: Absolute or relative path to a PDF or image file.

    Returns:
        {
            "bank": "<bank_id>",
            "confidence": <int 1-4>,
            "data": { "metadata": {...}, "tables": [[...]] }
        }
        or {"error": "<message>"} on failure.
    """
    # --- Validate input ---
    try:
        path = validate_input_path(path)
    except ValueError as exc:
        logger.error("Invalid input: %s", exc)
        return {"error": str(exc)}

    # --- OCR for bank detection ---
    is_pdf = path.lower().endswith(".pdf")
    if is_pdf:
        img = get_first_page_image(path)
        if img is None:
            return {"error": "Failed to convert PDF first page to image"}
        ocr_text = run_ocr(img)
    else:
        try:
            img = Image.open(path)
            ocr_text = run_ocr(img)
        except Exception as exc:
            logger.error("Failed to open image '%s': %s", path, exc)
            return {"error": f"Failed to open image: {exc}"}

    # --- MinerU full-document parsing ---
    md_text = run_mineru(path)
    if md_text is None:
        logger.warning("MinerU returned no output; bank detection will rely on OCR only.")

    # --- Bank detection ---
    bank, confidence = detect_bank(ocr_text, md_text)

    if not bank:
        logger.error("Bank not detected for file: %s", path)
        return {"error": "Bank not detected"}

    logger.info(
        "Detected bank: %s (confidence score: %d/6)", bank.upper(), confidence
    )

    # --- Load & run template ---
    module = load_template(bank)
    if module is None or not hasattr(module, "extract"):
        return {
            "bank": bank,
            "confidence": confidence,
            "error": f"No extraction template available for bank '{bank}'",
        }

    try:
        result = module.extract(bank, md_text or "", ocr_text)
    except Exception as exc:
        logger.error("Template extract() raised for bank '%s': %s", bank, exc, exc_info=True)
        return {
            "bank": bank,
            "confidence": confidence,
            "error": f"Extraction failed: {exc}",
        }

    return {
        "bank": bank,
        "confidence": confidence,
        "data": result,
    }


# =========================
# CLI ENTRY POINT
# =========================
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Bank statement data extractor")
    parser.add_argument("file", help="Path to the bank statement (PDF or image)")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    args = parser.parse_args()

    logging.getLogger().setLevel(getattr(logging, args.log_level))

    out = process(args.file)
    print(json.dumps(out, indent=2, ensure_ascii=False))