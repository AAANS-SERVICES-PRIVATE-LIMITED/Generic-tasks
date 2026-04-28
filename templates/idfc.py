import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an IDFC First Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[IDFC] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        tables = extract_tables(md_text)
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # --- Extract metadata from text lines ---
        address_parts = []
        in_address = False
        name_extracted = False

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                # Customer ID
                if "customer id" in low:
                    match = re.search(r"customer\s*id\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["customer_id"] = match.group(1)

                # Account Number
                elif "account no" in low:
                    match = re.search(r"account\s*no\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                # Statement Period
                elif "statement period" in low:
                    match = re.search(r"statement\s*period\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["period"] = match.group(1).strip()

                # Name (after ## heading)
                elif line.startswith("## ") and not name_extracted:
                    data["name"] = line.replace("## ", "").strip()
                    name_extracted = True

                # Address (lines starting with S/O: or containing address-like content)
                elif line.startswith("S/O:") or in_address:
                    in_address = True
                    if not any(skip in low for skip in ["email", "phone", "ifsc", "micr", "date of opening", "account status", "account type", "currency"]):
                        address_parts.append(line.strip())
                    else:
                        in_address = False

                # Email ID
                elif "email id" in low:
                    match = re.search(r"email\s*id\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["email"] = match.group(1).strip()

                # Phone Number
                elif "phone" in low:
                    match = re.search(r"phone\s*no\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["phone"] = match.group(1).strip()

                # IFSC
                elif "ifsc" in low:
                    match = re.search(r"ifsc\s*[:]\s*([A-Z0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(1).upper()

                # MICR Code
                elif "micr" in low:
                    match = re.search(r"micr\s*code\s*[:]\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["micr"] = match.group(1)

                # Handle line with multiple fields: DATE OF OPENING :15-Jan-2022 ACCOUNT STATUS :ACTIVE ACCOUNT TYPE :Zero Balance Savings Account CURRENCY :INR
                elif "date of opening" in low and "account status" in low and "account type" in low and "currency" in low:
                    # Parse all fields from this line
                    date_match = re.search(r"date\s*of\s*opening\s*[:]\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
                    if date_match:
                        data["date_of_opening"] = date_match.group(1).strip()

                    status_match = re.search(r"account\s*status\s*[:]\s*(\w+)", line, re.IGNORECASE)
                    if status_match:
                        data["account_status"] = status_match.group(1).strip()

                    type_match = re.search(r"account\s*type\s*[:]\s*(.+?)\s+currency", line, re.IGNORECASE)
                    if type_match:
                        data["account_type"] = type_match.group(1).strip()

                    currency_match = re.search(r"currency\s*[:]\s*(\w+)", line, re.IGNORECASE)
                    if currency_match:
                        data["currency"] = currency_match.group(1).strip()

                # Date of Opening (standalone)
                elif "date of opening" in low:
                    match = re.search(r"date\s*of\s*opening\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["date_of_opening"] = match.group(1).strip()

                # Account Status (standalone)
                elif "account status" in low:
                    match = re.search(r"account\s*status\s*[:]\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["account_status"] = match.group(1).strip()

                # Account Type (standalone)
                elif "account type" in low:
                    match = re.search(r"account\s*type\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["account_type"] = match.group(1).strip()

                # Currency (standalone)
                elif "currency" in low:
                    match = re.search(r"currency\s*[:]\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["currency"] = match.group(1).strip()

            except Exception as field_exc:
                logger.debug("[IDFC] Error parsing line '%s': %s", line, field_exc)

        if address_parts:
            data["address"] = " ".join(address_parts)

        # --- Extract amounts from first summary table ---
        if tables and len(tables) > 0:
            summary_table = tables[0]
            if len(summary_table) >= 2:
                headers = [h.lower() for h in summary_table[0]]
                values = summary_table[1]
                
                for i, header in enumerate(headers):
                    if i < len(values):
                        if "opening" in header:
                            data["opening_balance"] = values[i].strip()
                        elif "debit" in header and "total" in header:
                            data["total_debit"] = values[i].strip()
                        elif "credit" in header and "total" in header:
                            data["total_credit"] = values[i].strip()
                        elif "closing" in header:
                            data["closing_balance"] = values[i].strip()

        # --- Transaction tables (skip summary table) ---
        transaction_tables = tables[1:] if len(tables) > 1 else []

    except Exception as exc:
        logger.error("[IDFC] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
