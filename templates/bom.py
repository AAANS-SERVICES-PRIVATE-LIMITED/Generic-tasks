import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a BOM (Bank of Maharashtra) statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[BOM] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        tables = extract_tables(md_text)

        if tables:
            customer_table = tables[0]
            addr_lines = []  # Accumulate multi-row address

            for row in customer_table:
                if len(row) < 2:
                    continue
                try:
                    left  = row[0]
                    right = row[1]
                    left_low  = left.lower()
                    right_low = right.lower()

                    # --- Left cell: customer fields ---
                    if "name:" in left_low:
                        data["name"] = left.split(":", 1)[-1].strip()

                    elif "address:" in left_low:
                        # First address line
                        part = left.split(":", 1)[-1].strip()
                        if part:
                            addr_lines.append(part)

                    elif addr_lines and not any(kw in left_low for kw in [
                        "mobile", "email", "kyc", "ckyc", "primary", "date of birth",
                        "cif", "statement", "account", "branch",
                    ]):
                        # Continuation address lines (no recognized keyword)
                        val = left.strip()
                        if val:
                            addr_lines.append(val)

                    elif "mobile:" in left_low:
                        if addr_lines:
                            data["address"] = " ".join(addr_lines)
                            addr_lines = []
                        digits = re.sub(r"\D", "", left.split(":", 1)[-1])
                        if digits:
                            data["mobile"] = digits

                    elif "email" in left_low:
                        data["email"] = left.split(":", 1)[-1].strip()

                    elif "date of birth" in left_low:
                        data["dob"] = left.split(":", 1)[-1].strip()

                    elif "cif number" in left_low:
                        data["cif"] = left.split(":", 1)[-1].strip()

                    elif "statement date" in left_low:
                        data["statement_date"] = left.split(":", 1)[-1].strip()

                    # --- Right cell: branch & account fields ---
                    if "ifsc" in right_low:
                        # May be "Branch No:00454 Branch IFSC:MAHB0000454"
                        ifsc_m = re.search(r"ifsc[:\s]+([A-Z0-9]+)", right, re.IGNORECASE)
                        if ifsc_m:
                            data["ifsc"] = ifsc_m.group(1)
                        branch_no_m = re.search(r"branch\s*no[:\s]+(\d+)", right, re.IGNORECASE)
                        if branch_no_m:
                            data["branch_no"] = branch_no_m.group(1)

                    elif "branch name" in right_low:
                        data["branch"] = right.split(":", 1)[-1].strip()

                    elif "account no" in right_low:
                        match = re.search(r"account\s*no[:\s]+(\d+)", right, re.IGNORECASE)
                        if match:
                            data["account_number"] = match.group(1)

                    elif "accountopen date" in right_low or "account open date" in right_low:
                        data["account_open_date"] = right.split(":", 1)[-1].strip()

                    elif "account type" in right_low:
                        data["account_type"] = right.split(":", 1)[-1].strip()

                    elif "total balance" in right_low:
                        data["total_balance"] = right.split(":", 1)[-1].strip()

                    elif "available balance" in right_low:
                        data["available_balance"] = right.split(":", 1)[-1].strip()

                    elif "nomination flag" in right_low:
                        data["nomination"] = right.split(":", 1)[-1].strip()

                except Exception as cell_exc:
                    logger.debug("[BOM] Error parsing cell: %s", cell_exc)

            # Flush any remaining address lines
            if addr_lines and not data.get("address"):
                data["address"] = " ".join(addr_lines)

        transaction_tables = tables[1:] if len(tables) > 1 else []

    except Exception as exc:
        logger.error("[BOM] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
