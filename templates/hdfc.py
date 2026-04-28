import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an HDFC bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[HDFC] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        tables = extract_tables(md_text)
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # --- Parse first table as metadata (name, address, etc.) ---
        if tables and len(tables) > 0:
            first_table = tables[0]
            if first_table:
                # First row is usually the name
                if len(first_table) > 0 and first_table[0]:
                    data["name"] = first_table[0][0].strip()
                # Other rows may contain address, joint holders, etc.
                address_parts = []
                for row in first_table[1:]:
                    if row and row[0] and row[0].strip():
                        cell = row[0].strip()
                        if "joint" not in cell.lower():
                            address_parts.append(cell)
                if address_parts:
                    data["address"] = " ".join(address_parts)

        # --- Parse text lines for key-value metadata ---
        for line in lines:
            low = line.lower()

            try:
                # Period range — From and To may be on separate lines
                if re.match(r"^from[\uff1a:]\s*", line, re.IGNORECASE):
                    data["from_date"] = re.sub(r"^from[\uff1a:]\s*", "", line, flags=re.IGNORECASE).strip()
                    to_match = re.search(r"to[\uff1a:]\s*(.+)", line, re.IGNORECASE)
                    if to_match:
                        data["to_date"] = to_match.group(1).strip()

                elif re.match(r"^to[\uff1a:]\s*", line, re.IGNORECASE):
                    data["to_date"] = re.sub(r"^to[\uff1a:]\s*", "", line, flags=re.IGNORECASE).strip()

                elif "nomination" in low:
                    match = re.search(r"nomination\s*[:：]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["nomination"] = match.group(1).strip()

                elif "account branch" in low:
                    match = re.search(r"account\s*branch\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch"] = match.group(1).strip()

                elif "address" in low and "last" not in low:
                    match = re.search(r"address\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["address"] = match.group(1).strip()

                elif "city" in low:
                    match = re.search(r"city\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["city"] = match.group(1).strip()

                elif "state" in low:
                    match = re.search(r"state\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["state"] = match.group(1).strip()

                elif "phone" in low or "phonc" in low:
                    # Handle OCR variants like "Phonc 0o :" — allow up to 8 chars between keyword and colon
                    match = re.search(r"ph[o0]n[ce].{0,8}[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["phone"] = match.group(1).strip()

                elif "od limit" in low:
                    match = re.search(r"od\s*limit\s*[:：]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["od_limit"] = match.group(1).strip()

                elif "currency" in low:
                    match = re.search(r"currency\s*[:]\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["currency"] = match.group(1).strip()

                elif "email" in low:
                    match = re.search(r"email\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["email"] = match.group(1).strip()

                elif "cust id" in low:
                    match = re.search(r"cust\s*id\s*[:]\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["customer_id"] = match.group(1)

                elif "account no" in low and "number" not in low:
                    match = re.search(r"account\s*no\s*[:]\s*([0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif re.search(r"ac\s*open\s*dat[ce]|account\s*open\s*dat[ce]", line, re.IGNORECASE):
                    # Handle OCR: "ACOpen Datc" or "AC Open Date"
                    match = re.search(r"(?:ac|account)\s*open\s*dat[ce]\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["account_open_date"] = match.group(1).strip()

                elif "account status" in low:
                    match = re.search(r"account\s*status\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["account_status"] = match.group(1).strip()

                elif "ifsc" in low:
                    match = re.search(r"ifsc\s*[:]\s*([A-Z0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(1).upper()
                    # MICR often appears on the same line as IFSC
                    micr_match = re.search(r"micr\s*[:]?\s*(\d{9})", line, re.IGNORECASE)
                    if micr_match and not data.get("micr"):
                        data["micr"] = micr_match.group(1)

                elif "micr" in low:
                    match = re.search(r"micr\s*[:]?\s*([0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["micr"] = match.group(1)

                elif "branch code" in low:
                    match = re.search(r"branch\s*code\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch_code"] = match.group(1).strip()

                elif "product code" in low:
                    match = re.search(r"product\s*code\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["product_code"] = match.group(1).strip()

            except Exception as field_exc:
                logger.debug("[HDFC] Error parsing line '%s': %s", line, field_exc)

        # --- Transaction tables are tables after the first one ---
        transaction_tables = tables[1:] if len(tables) > 1 else []

    except Exception as exc:
        logger.error("[HDFC] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
