import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a Kotak Mahindra Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[Kotak] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                if i == 0 and line.strip():
                    data["name"] = line.strip()

                elif "period" in low:
                    match = re.search(r"period\s*[:\-]?\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["period"] = match.group(1).strip()

                elif "cust.reln.no" in low or "cust. reln. no" in low:
                    match = re.search(r"cust\.\s*reln\.\s*no\s*[:\-]?\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["customer_relation_no"] = match.group(1)

                elif "account no" in low and "number" not in low:
                    match = re.search(r"account\s*no\s*[:\-]?\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif "currency" in low:
                    match = re.search(r"currency\s*[:\-]?\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["currency"] = match.group(1)

                elif "branch" in low and "ifsc" not in low:
                    # Only extract if the line itself has a colon+value (e.g. "Branch: XYZ")
                    # Bare "Branch" labels with no value on the same line are skipped
                    match = re.search(r"branch\s*[:\-]\s*(.+)", line, re.IGNORECASE)
                    if match and match.group(1).strip():
                        data["branch"] = match.group(1).strip()

                elif "ifsc" in low:
                    match = re.search(r"ifsc\s*code\s*[:\-]?\s*([A-Za-z0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(1).upper()

                elif "statement date" in low:
                    match = re.search(r"statement\s*date\s*[:\-]?\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["statement_date"] = match.group(1).strip()

                elif "nominee" in low:
                    match = re.search(r"nominee\s*registered\s*[:\-]?\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["nominee_registered"] = match.group(1)

            except Exception as field_exc:
                logger.debug("[Kotak] Error parsing line '%s': %s", line, field_exc)

        # Address: lines between S/O marker and the IFSC line
        addr_lines = []
        capturing = False
        for line in lines:
            low = line.lower()
            if re.match(r"^s/o", line, re.IGNORECASE) or (capturing and "ifsc" not in low and "statement" not in low and not line.startswith("#")):
                capturing = True
                addr_lines.append(line.strip())
            elif "ifsc" in low:
                break
        if addr_lines:
            data["address"] = " ".join(addr_lines)

        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[Kotak] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
