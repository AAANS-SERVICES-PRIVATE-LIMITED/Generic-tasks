import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an Airtel telecom bill."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[Airtel] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # --- Name: first line that starts with a title prefix (Mr./Mrs./Ms./Dr.) ---
        name_idx = -1
        for i, line in enumerate(lines[:10]):
            if re.match(r"^(mr|mrs|ms|dr)\.?\s+\S+", line, re.IGNORECASE):
                data["customer_name"] = line.strip()
                name_idx = i
                break

        # --- Address: lines after name until image link / phone-only / known keyword ---
        if name_idx >= 0:
            addr_parts = []
            for line in lines[name_idx + 1:]:
                low = line.lower()
                # Stop at image links, phone-only, or billing keyword lines
                if (line.startswith("![")
                        or line.strip().isdigit()
                        or any(kw in low for kw in [
                            "airtel number", "bill number", "bill date",
                            "bill period", "relationship number", "gst",
                            "relation", "credit limit", "security", "pay by"
                        ])):
                    break
                # Collect address lines — include those with digits (pincode, flat numbers)
                if line.strip():
                    addr_parts.append(line.strip())
            if addr_parts:
                data["address"] = " ".join(addr_parts)

        # --- Metadata: line-by-line scan ---
        for i, line in enumerate(lines):
            low = line.lower()

            try:
                # Airtel number
                if "airtel number" in low or "airtel no" in low:
                    match = re.search(r"airtel\s+n(?:umber|o)[.\s:]*([0-9\s]+)", line, re.IGNORECASE)
                    if match:
                        data["airtel_number"] = match.group(1).replace(" ", "").strip()

                # Relationship number — handles OCR split "Relations hip number"
                elif re.search(r"relat\w*\s+\w*\s*number", line, re.IGNORECASE):
                    match = re.search(r"number\s+([0-9\s]+)", line, re.IGNORECASE)
                    if match:
                        data["relationship_number"] = match.group(1).replace(" ", "").strip()

                # Bill number — handles OCR "Bil number" (one l)
                elif re.search(r"bil+\s+number", low):
                    match = re.search(r"bil+\s+number\s+([0-9\s]+)", line, re.IGNORECASE)
                    if match:
                        data["bill_number"] = match.group(1).replace(" ", "").strip()

                # Bill date — handles middle-dot separator "21·Apr-2019"
                elif "bill date" in low:
                    match = re.search(r"bill\s+date\s*[:\s·]+(.+)", line, re.IGNORECASE)
                    if match:
                        data["bill_date"] = match.group(1).strip()

                # Bill period
                elif "bill period" in low:
                    match = re.search(r"bill\s+period\s*[:\s]+(.+)", line, re.IGNORECASE)
                    if match:
                        data["bill_period"] = match.group(1).strip()

                # Pay by date
                elif "pay by date" in low:
                    match = re.search(r"pay\s+by\s+date\s*[:\s]+(.+)", line, re.IGNORECASE)
                    if match:
                        data["pay_by_date"] = match.group(1).strip()

                # Credit limit
                elif "credit limit" in low:
                    match = re.search(r"credit\s+limit\s*[:\s]+([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["credit_limit"] = match.group(1)

                # Security deposit — handles OCR split "Security de posit"
                elif "security" in low and ("deposit" in low or "posit" in low):
                    match = re.search(r"security\s+de?\s*posit\s*[:\s]+([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["security_deposit"] = match.group(1)

                # Amount due (standalone)
                elif "amount due" in low:
                    match = re.search(r"amount\s+due\s*[:\s]*([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["amount_due"] = match.group(1)

                # GST number
                elif "gst" in low and "uid" in low:
                    match = re.search(r"gst\s+mo/uid\s+no\s*[:\s]*([A-Z0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["gst_number"] = match.group(1)

            except Exception as field_exc:
                logger.debug("[Airtel] Error parsing line '%s': %s", line, field_exc)

        # Extract tables (do NOT store in data dict)
        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[Airtel] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
