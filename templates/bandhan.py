import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a Bandhan Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[Bandhan] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        # --- First HTML table: Name and Address ---
        first_table_match = re.search(r"<table>.*?</table>", md_text, re.DOTALL | re.IGNORECASE)
        if first_table_match:
            html = first_table_match.group(0)
            rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL | re.IGNORECASE)
            
            address_parts = []
            for row in rows:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
                if len(cells) >= 2:
                    try:
                        key = clean(cells[0]).lower()
                        value = clean(cells[1])

                        if "name" in key:
                            data["name"] = value.replace(":", "").strip()
                        elif "address" in key:
                            addr_line = value.replace(":", "").strip()
                            if addr_line:
                                address_parts.append(addr_line)
                        elif not key and value.strip():
                            # Continuation: empty first cell, value in second — still address
                            addr_line = value.strip()
                            if addr_line.lower() not in ["name", "address"]:
                                address_parts.append(addr_line)
                    except Exception as cell_exc:
                        logger.debug("[Bandhan] Error parsing table cell: %s", cell_exc)
                elif len(cells) == 1:
                    addr_line = clean(cells[0]).strip()
                    if addr_line and addr_line.lower() not in ["name", "address"]:
                        address_parts.append(addr_line)
            
            if address_parts:
                data["address"] = " ".join(address_parts)

        # --- Text-based metadata ---
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        for line in lines:
            low = line.lower()

            try:
                if "opening balance" in low:
                    match = re.search(r"opening\s+balance\s*[:]\s*([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["opening_balance"] = match.group(1)

                elif "branch code" in low:
                    match = re.search(r"branch\s+code\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["branch_code"] = match.group(1)

                elif "branch name" in low:
                    match = re.search(r"branch\s+name\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch_name"] = match.group(1).strip()

                elif "branch address" in low:
                    match = re.search(r"branch\s+address\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch_address"] = match.group(1).strip()

                elif "branch phone" in low:
                    # Handle with or without colon: "Branch Phone No. 8017618992"
                    match = re.search(r"branch\s+phone[^:]*[:\s]+([\d-]+)", line, re.IGNORECASE)
                    if match:
                        data["branch_phone"] = match.group(1)

                elif "branch email" in low:
                    match = re.search(r"branch\s+email\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        email = match.group(1).strip()
                        if email and email != ":":
                            data["branch_email"] = email

                elif "ifsc" in low:
                    match = re.search(r"ifsc\s*[:]\s*([A-Z0-9]+)", line, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(1)

                elif "micr" in low:
                    match = re.search(r"micr\s+code\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["micr"] = match.group(1)

                elif "branch gstin" in low:
                    match = re.search(r"branch\s+gstin\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch_gstin"] = match.group(1).strip()

                elif "customer number" in low:
                    match = re.search(r"customer\s+number\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["customer_number"] = match.group(1)

                elif "account number" in low:
                    match = re.search(r"account\s+number\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif "product type" in low:
                    match = re.search(r"product\s+type\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["product_type"] = match.group(1).strip()

                elif "account type" in low and "mab" not in low:
                    match = re.search(r"account\s+type\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["account_type"] = match.group(1).strip()

                elif "mab" in low or "qab" in low:
                    match = re.search(r"mab\s*/?\s*qab\s*[:]\s*([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["mab_qab"] = match.group(1)

                elif "email" in low and "branch" not in low:
                    # Handle OCR noise between "Email" and ":" e.g. "Email 1D : john@gmail.com"
                    match = re.search(r"email[^:]*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        email = match.group(1).strip()
                        if email and "@" in email:
                            data["email"] = email

                elif "nominee" in low and "registration" in low:
                    match = re.search(r"nominee\s+registration\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["nominee_registration"] = match.group(1).strip()

                elif "closing balance" in low:
                    match = re.search(r"closing\s+balance\s*[:]\s*([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["closing_balance"] = match.group(1)

            except Exception as field_exc:
                logger.debug("[Bandhan] Error parsing line '%s': %s", line, field_exc)

        # --- Extract transaction tables ---
        tables = extract_tables(md_text)
        if tables:
            # Skip first table (metadata table), keep only transaction tables
            transaction_tables = tables[1:] if len(tables) > 1 else []
        else:
            transaction_tables = []

    except Exception as exc:
        logger.error("[Bandhan] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
