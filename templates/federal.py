import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a Federal Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[Federal] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        tables = extract_tables(md_text)

        # --- First table: account metadata ---
        # Federal Bank table has 6 columns: key1 | sep(,) | value1 | key2 | sep(：) | value2
        # After filtering empty cells, pattern becomes: key | sep? | value | key | sep? | value
        _SEPARATORS = {",", "，", "：", ":", "|"}

        KNOWN_KEYS = [
            "name", "branch_name", "branch", "communication_address",
            "branch_sol", "account_number", "customer_id", "customerid",
            "address_last_updated", "regd._mobile_number", "mobile",
            "account_open_date", "email", "account_status", "type_of_account",
            "type_oraccount", "mode_of_operation", "scheme", "joint_holders",
            "ifsc", "micr", "swift", "nomination", "nominee",
            "effective_available_balance", "available_balance",
            "currency", "opening_balance", "date_of_issue",
        ]

        if tables:
            for row in tables[0]:
                try:
                    cells = [cell.strip().lstrip(":") for cell in row if cell.strip()]

                    i = 0
                    while i < len(cells):
                        cell = cells[i].lower().replace(":", "").replace(" ", "_")

                        if not any(k in cell for k in KNOWN_KEYS):
                            i += 1
                            continue

                        # Determine value — skip separator cell if present at i+1
                        if i + 1 >= len(cells):
                            i += 1
                            continue

                        raw_next = cells[i + 1].strip()
                        is_sep = (raw_next in _SEPARATORS or
                                  (len(raw_next) <= 1 and not raw_next.isalnum()))
                        if is_sep and i + 2 < len(cells):
                            value = cells[i + 2]
                            i += 3
                        else:
                            value = raw_next
                            i += 2

                        # Map cell key to data field
                        if "name" in cell and "branch" not in cell:
                            data["name"] = value
                        elif "branch_name" in cell or (cell == "branch" and "sol" not in cell):
                            data["branch"] = value
                        elif "communication_address" in cell:
                            data["communication_address"] = value
                        elif "branch_sol" in cell:
                            data["branch_id"] = value
                        elif "account_number" in cell:
                            data["account_number"] = value
                        elif "customer_id" in cell or "customerid" in cell:
                            data["customer_id"] = value
                        elif "address_last_updated" in cell:
                            data["address_updated"] = value
                        elif "regd._mobile_number" in cell or "mobile" in cell:
                            data["mobile"] = value
                        elif "account_open_date" in cell:
                            data["account_open_date"] = value
                        elif "email" in cell and "ld" not in cell and "1d" not in cell:
                            data["email"] = value.replace(" ", "")
                        elif "account_status" in cell:
                            data["account_status"] = value
                        elif "type_of_account" in cell or "type_oraccount" in cell:
                            # Value may be "email@x.com Savings" concatenated due to OCR
                            if " " in value:
                                parts = value.rsplit(" ", 1)
                                data.setdefault("email", parts[0].strip())
                                data["account_type"] = parts[1].strip()
                            else:
                                data["account_type"] = value
                        elif "mode_of_operation" in cell:
                            data["mode_of_operation"] = value
                        elif "scheme" in cell:
                            data["scheme"] = value
                        elif "joint_holders" in cell:
                            data["joint_holders"] = value
                        elif "ifsc" in cell:
                            data["ifsc"] = value
                        elif "micr" in cell:
                            data["micr"] = value
                        elif "swift" in cell:
                            data["swift"] = value
                        elif "nomination" in cell or "nominee" in cell:
                            data["nomination"] = value
                        elif "effective_available_balance" in cell or "available_balance" in cell:
                            data["available_balance"] = value
                        elif "currency" in cell:
                            data["currency"] = value
                        elif "opening_balance" in cell:
                            data["opening_balance"] = value
                        elif "date_of_issue" in cell:
                            data["date_of_issue"] = value

                except Exception as cell_exc:
                    logger.debug("[Federal] Error parsing metadata row: %s", cell_exc)

        # --- Statement period from text ---
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]
        for line in lines:
            try:
                match = re.search(
                    r"Statement of Account for month the ([A-Za-z]+)-(\d{4})",
                    line, re.IGNORECASE,
                )
                if match:
                    data["statement_month"] = match.group(1)
                    data["statement_year"] = match.group(2)
                    break
            except Exception:
                pass

        transaction_tables = tables[1:] if len(tables) > 1 else tables

    except Exception as exc:
        logger.error("[Federal] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
