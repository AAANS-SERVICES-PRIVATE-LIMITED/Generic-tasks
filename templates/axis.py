import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an Axis Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[Axis] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # Name — line above "Joint Holder"; address — lines between name and MOBILE NO
        name_idx = -1
        for i, line in enumerate(lines):
            try:
                if "joint holder" in line.lower():
                    if i > 0:
                        name_line = lines[i - 1]
                        if not name_line.startswith("#") and len(name_line.split()) >= 2:
                            data["name"] = name_line
                            name_idx = i - 1
                    break
            except Exception as field_exc:
                logger.debug("[Axis] name-detection error: %s", field_exc)

        # Address: lines between name and MOBILE NO
        if name_idx >= 0:
            addr_lines = []
            for line in lines[name_idx + 2:]:
                if re.search(r"mobile\s*no", line, re.IGNORECASE):
                    break
                if not line.startswith("#") and "joint" not in line.lower():
                    addr_lines.append(line.strip())
            if addr_lines:
                data["address"] = " ".join(addr_lines)

        for line in lines:
            low = line.lower()

            try:
                if "customer id" in low:
                    data["customer_id"] = line.split(":")[-1].strip()

                elif "micr" in low:
                    data["micr_code"] = line.split(":")[-1].strip()

                elif "mobile no" in low and "registered" not in low:
                    digits = re.sub(r"\D", "", line)
                    if digits:
                        data["mobile_no"] = digits

                elif "registered mobile" in low:
                    data["registered_mobile"] = line.split(":")[-1].strip()

                elif "email" in low:
                    data["email"] = line.split(":")[-1].strip()

                elif "ifsc" in low:
                    data["ifsc"] = line.split(":")[-1].strip()

                elif "nominee" in low:
                    data["nominee"] = line.split(":")[-1].strip()

                elif "pan" in low:
                    pan_match = re.search(r"[:\s]\s*([A-Z]{5}\d{4}[A-Z])", line)
                    if pan_match:
                        data["pan"] = pan_match.group(1)
                    else:
                        pan_part = re.sub(r"[^A-Za-z0-9]", "", line.split(":")[-1].strip())
                        if len(pan_part) == 10:
                            data["pan"] = pan_part.upper()

                elif "statement of account no" in low or ("statement of account" in low and ":" in line):
                    match = re.search(r"account\s*no\s*[:\s]+(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif "for the period" in low or ("from" in low and "to" in low and re.search(r"\d{2}-\d{2}-\d{4}", line)):
                    from_m = re.search(r"from\s*[:\s]+([\d]{2}-[\d]{2}-[\d]{4})", line, re.IGNORECASE)
                    to_m = re.search(r"to\s*[:\s]+([\d]{2}-[\d]{2}-[\d]{4})", line, re.IGNORECASE)
                    if from_m:
                        data["statement_from"] = from_m.group(1)
                    if to_m:
                        data["statement_to"] = to_m.group(1)

                elif "scheme" in low:
                    data["scheme"] = line.split(":")[-1].strip()

            except Exception as field_exc:
                logger.debug("[Axis] Error parsing line '%s': %s", line, field_exc)

        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[Axis] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}