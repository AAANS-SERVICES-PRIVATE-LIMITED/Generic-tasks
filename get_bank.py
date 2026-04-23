import os
import re
import subprocess
import json
import importlib.util
import shutil
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# =========================
# CONFIG
# =========================
TEMPLATE_PATH = r"E:\PROJECTS\f-ai\bank_data_extraction\tools_test\templates"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# =========================
# BANK DETECTION (improved)
# =========================
BANK_PATTERNS = {
    # Longer/more specific patterns first to avoid substring matches
    r"\bstate\s*bank\s*of\s*india\b|\bs\s*b\s*i\b|sbi": "sbi",
    r"\bbank\s*of\s*baroda\b|\bb\s*o\s*b\b|\bbob\b": "bob",
    r"\bpunjab\s*national\s*bank\b|\bp\s*n\s*b\b|\bpnb\b": "pnb",
    r"\bcanara\s*bank\b|\bcanara\b": "canara",
    r"\bunion\s*bank\s*of\s*india\b|\bu\s*b\s*i\b|\bubi\b": "ubi",
    r"\bcentral\s*bank\s*of\s*india\b|\bc\s*b\s*i\b|\bcbi\b": "cbi",
    r"\bbank\s*of\s*india\b|\bb\s*o\s*i\b|\bboi\b": "boi",
    r"\bindian\s*overseas\s*bank\b|\bi\s*o\s*b\b|\biob\b": "iob",
    r"\bbank\s*of\s*maharashtra\b|\bb\s*o\s*m\b|\bbom\b|\bmaharashtra\s*bank\b": "bom",
    r"\bindian\s*bank\b": "indian",
    r"\buco\s*bank\b|\bu\s*c\s*o\b": "uco",
    r"\bpunjab\s*(?:&\s*|and\s*)?sind\s*bank\b|\bp\s*s\s*b\b|\bpsb\b": "psb",
    r"\baxis\s*bank\b|\baxis\b": "axis",
    # Additional banks
    r"\bhdfc\s*bank\b|\bhdfc\b": "hdfc",
    r"\bicici\s*bank\b|\bicici\b": "icici",
    r"\bkotak\s*(?:mahindra\s*)?bank\b|\bkotak\b": "kotak",
    r"\b_YES_\s*BANK_\b|\byes\s*bank\b": "yes",
    r"\bidbi\s*bank\b|\bidbi\b": "idbi",
    r"\bindusind\s*bank\b|\bindusind\b": "indusind",
    r"\bfederal\s*bank\b|\bfederal\b": "federal",
    r"\brbl\s*bank\b|\brbl\b": "rbl",
    r"\bj\s*&\s*k\s*bank\b|\bjammu\s*and\s*kashmir\s*bank\b": "jk",
    r"\bkarnataka\s*bank\b": "karnataka",
    r"\bsouth\s*indian\s*bank\b": "south_indian",
    r"\bcity\s*union\s*bank\b": "city_union",
    r"\btamilnad\s*mercantile\s*bank\b|\btmb\b": "tmb",
    r"\bdcb\s*bank\b|\bdcb\b": "dcb",
    r"\bbandhan\s*bank\b|\bbandhan\b": "bandhan",
}


# IFSC code prefix to bank mapping (first 4 chars of IFSC)
IFSC_BANK_MAP = {
    "SBIN": "sbi",
    "BARB": "bob",
    "PUNB": "pnb",
    "CNRB": "canara",
    "UTBI": "ubi",
    "CBIN": "cbi",
    "BKID": "boi",
    "IOBA": "iob",
    "MAHB": "bom",
    "IDIB": "indian",
    "UCBA": "uco",
    "PSIB": "psb",
    "UTIB": "axis",
    "HDFC": "hdfc",
    "ICIC": "icici",
    "KKBK": "kotak",
    "YESB": "yes",
    "IBKL": "idbi",
    "INDB": "indusind",
    "FDRL": "federal",
    "RATN": "rbl",
    "JAKA": "jk",
    "KARB": "karnataka",
    "SIBL": "south_indian",
    "CIUB": "city_union",
    "TMBL": "tmb",
    "DCBL": "dcb",
    "BDBL": "bandhan",
}


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_bank_from_text(text):
    """Detect bank from single text source. Returns (bank_name, method) or (None, None)."""
    if not text:
        return None, None

    original_text = text
    normalized_text = normalize(text)

    # Search 1: Bank name pattern matching
    bank_from_name = None
    best_score = 0

    for pattern, bank in BANK_PATTERNS.items():
        match = re.search(pattern, normalized_text)
        if match:
            score = len(match.group(0))
            if score > best_score:
                best_score = score
                bank_from_name = bank

    # Search 2: IFSC code matching (strict - only full IFSC patterns)
    bank_from_ifsc = None
    text_upper = original_text.upper()

    # Look for full IFSC pattern: 4 letters + 0/O + 6 alphanumeric
    # Examples: SBIN0001234, UTBI0MER123, CBIN0284518
    ifsc_matches = re.findall(r'\b([A-Z]{4}[0O][A-Z0-9]{6,7})\b', text_upper)
    for ifsc in ifsc_matches:
        bank_code = ifsc[:4]  # First 4 chars
        if bank_code in IFSC_BANK_MAP:
            bank_from_ifsc = IFSC_BANK_MAP[bank_code]
            break

    return bank_from_name, bank_from_ifsc


def detect_bank(ocr_text, mineru_text=None):
    """Detect bank using OCR and MinerU text with scoring system.

    Logic:
    1. Get bank_from_name and bank_from_ifsc from OCR text
    2. If mineru_text provided, get same from MinerU
    3. Score: if 2+ sources agree on same bank, return it
    4. If conflict, return None
    """
    scores = {}

    # Analyze OCR text
    ocr_name, ocr_ifsc = detect_bank_from_text(ocr_text)

    if ocr_name:
        scores[ocr_name] = scores.get(ocr_name, 0) + 1
    if ocr_ifsc:
        scores[ocr_ifsc] = scores.get(ocr_ifsc, 0) + 1

    # Analyze MinerU text if provided
    mineru_name, mineru_ifsc = None, None
    if mineru_text:
        mineru_name, mineru_ifsc = detect_bank_from_text(mineru_text)

        if mineru_name:
            scores[mineru_name] = scores.get(mineru_name, 0) + 1
        if mineru_ifsc:
            scores[mineru_ifsc] = scores.get(mineru_ifsc, 0) + 1

    # Find bank with score >= 2 (at least 2 sources agree)
    best_bank = None
    best_score = 0

    for bank, score in scores.items():
        if score >= 2 and score > best_score:
            best_score = score
            best_bank = bank

    # If no consensus (score >= 2), check if we have at least one strong detection
    if not best_bank:
        # Prefer name match over IFSC
        if ocr_name:
            return ocr_name
        if mineru_name:
            return mineru_name
        if ocr_ifsc:
            return ocr_ifsc
        if mineru_ifsc:
            return mineru_ifsc

    return best_bank


# =========================
# OCR
# =========================
def extract_text(path):
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    return text, text.split()


# =========================
# MINERU
# =========================
def run_mineru(path):
    tmp = "tmp_mineru"
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)

    cmd = ["mineru", "-p", path, "-o", tmp, "-b", "pipeline"]

    env = os.environ.copy()
    env["MINERU_DISABLE_VLM"] = "true"
    env["CUDA_VISIBLE_DEVICES"] = ""

    res = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if res.returncode != 0:
        print(res.stderr)
        return None

    md = None
    md_files = []
    for r, _, f in os.walk(tmp):
        for file in f:
            if file.endswith(".md"):
                md_files.append(os.path.join(r, file))

    # Read the largest md file (usually the main content)
    if md_files:
        largest_file = max(md_files, key=lambda f: os.path.getsize(f))
        with open(largest_file, "r", encoding="utf-8") as fp:
            md = fp.read()

    shutil.rmtree(tmp)
    return md


# =========================
# PDF TO IMAGE (for OCR detection)
# =========================
def get_first_page_image(pdf_path):
    """Convert first page of PDF to PIL Image for OCR."""
    images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
    if images:
        return images[0]
    return None


def extract_text_from_image(img):
    """Run tesseract OCR on PIL Image."""
    text = pytesseract.image_to_string(img)
    return text, text.split()


# =========================
# LOAD TEMPLATE DYNAMICALLY
# =========================
def load_template(bank_name):
    file_path = os.path.join(TEMPLATE_PATH, f"{bank_name}.py")

    if not os.path.exists(file_path):
        return None

    spec = importlib.util.spec_from_file_location(bank_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


# =========================
# MAIN
# =========================
def process(path):
    # Check if input is PDF
    is_pdf = path.lower().endswith('.pdf')

    if is_pdf:
        img = get_first_page_image(path)
        if img is None:
            return {"error": "Failed to convert PDF to image"}
        ocr_text, _ = extract_text_from_image(img)
    else:
        ocr_text, _ = extract_text(path)

    # Run MinerU first to get its text for bank detection
    md = run_mineru(path)
    mineru_text = md if md else None

    # Detect bank using both OCR and MinerU text with scoring
    bank = detect_bank(ocr_text, mineru_text)

    print("\n" + "="*50)
    print(f"DETECTED BANK: {bank.upper()}")
    print("="*50)

    if not bank:
        print("\nERROR: Bank not detected. Stopping execution.")
        return {"error": "Bank not detected"}

    # load template
    module = load_template(bank)

    if module and hasattr(module, "extract"):
        # Pass OCR text as well for templates that need it (like BOB for grey box data)
        result = module.extract(bank, md, ocr_text)
    else:
        result = {"error": "template not found"}

    return {
        "bank": bank,
        "data": result
    }


# =========================
# RUN
# =========================
if __name__ == "__main__":
    path = r"E:\PROJECTS\f-ai\bank_data_extraction\data_png\bom.png"

    out = process(path)

    print("\nFINAL OUTPUT:\n")
    print(json.dumps(out, indent=2))