import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a UBI (Union Bank of India) statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[UBI] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                if "union bank of india" in low:
                    if i >= 1 and not data.get("name"):
                        prev = lines[i - 1]
                        if prev.replace(" ", "").isalpha() and len(prev) > 2:
                            data["name"] = prev
                    continue

                # Branch — UBI may use space instead of colon: "Branch JAMNAGAR MUN CORPO E C"
                elif "branch" in low:
                    match = re.search(r"branch[-:\s]+(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch"] = match.group(1).strip()

                # Customer Id (handle OCR typo "ld" → "id")
                elif "customer" in low and ("id" in low or "ld" in low):
                    match = re.search(r"customer\s*[il]d\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["customer_id"] = match.group(1)
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        data["customer_id"] = lines[i + 1].strip()

                elif "account no" in low:
                    match = re.search(r"account\s*no\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        data["account_number"] = lines[i + 1].strip()

                elif "mobile no" in low or "mobile" in low:
                    match = re.search(r"mobile\s*(?:no)?\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["mobile"] = match.group(1)
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        data["mobile"] = lines[i + 1].strip()

                # Catch standalone phone-like numbers (10 or 12 digits) with no label
                elif line.strip().isdigit() and len(line.strip()) in [10, 12] and not data.get("mobile"):
                    data["mobile"] = line.strip()

                elif re.search(r"account\s+curren[a-z]+", low):  # handles "currency" and OCR "currenoy"
                    match = re.search(r"account\s+curren[a-z]+\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["currency"] = match.group(1)
                    elif i + 1 < len(lines):
                        data["currency"] = lines[i + 1].strip()

                elif "account type" in low:
                    match = re.search(r"account\s*type\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["account_type"] = match.group(1).strip()
                    elif i + 1 < len(lines):
                        data["account_type"] = lines[i + 1].strip()

                elif "e-mail" in low or "email" in low:
                    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", line)
                    if match:
                        data["email"] = match.group(0)
                    elif i + 1 < len(lines) and "@" in lines[i + 1]:
                        data["email"] = lines[i + 1].strip()

                elif re.search(r"statement\s+d?\s*ate", low):  # handles "Statement D ate" OCR split
                    match = re.search(r"statement\s+d?\s*ate[:\s]+(.+)", line, re.IGNORECASE)
                    if match:
                        data["statement_date"] = match.group(1).strip()
                    elif i + 1 < len(lines):
                        data["statement_date"] = lines[i + 1].strip()

                elif "statement period" in low:
                    match = re.search(
                        r"statement\s*period\s*from[-\s]*([\d/]+)\s*to\s*([\d/]+)",
                        line, re.IGNORECASE,
                    )
                    if match:
                        data["statement_from"] = match.group(1)
                        data["statement_to"] = match.group(2)
                    elif i + 1 < len(lines):
                        match2 = re.search(
                            r"from[-\s]*([\d/]+)\s*to\s*([\d/]+)", lines[i + 1], re.IGNORECASE
                        )
                        if match2:
                            data["statement_from"] = match2.group(1)
                            data["statement_to"] = match2.group(2)

                elif line.strip().isdigit() and len(line.strip()) == 6:
                    data["zip"] = line.strip()

                # UBI format: value comes BEFORE label — look BACKWARD one line
                elif "city" in low:
                    if i > 0:
                        city_val = lines[i - 1].strip()
                        if city_val and city_val.lower() not in ["state", "stae", "country", "zip", "india", "## statement of account"]:
                            data["city"] = city_val

                elif "state" in low or "stae" in low:
                    if i > 0:
                        state_val = lines[i - 1].strip()
                        if state_val and state_val.lower() not in ["city", "country", "zip"]:
                            data["state"] = state_val

                elif "country" in low:
                    if i > 0:
                        country_val = lines[i - 1].strip()
                        if country_val and country_val.lower() not in ["state", "stae", "city", "zip"]:
                            data["country"] = country_val

            except Exception as field_exc:
                logger.debug("[UBI] Error parsing line '%s': %s", line, field_exc)

        # Fallback: derive name from first lines if still missing
        if not data.get("name"):
            for line in lines[:5]:
                if line.replace(" ", "").isalpha() and len(line) > 3 and line.lower() not in ["statement of account"]:
                    data["name"] = line
                    break

        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[UBI] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
