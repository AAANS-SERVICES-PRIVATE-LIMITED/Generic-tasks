import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a CBI (Central Bank of India) statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[CBI] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        for line in lines:
            low = line.lower()

            try:
                if "statement for a/c" in low:
                    match = re.search(r"statement\s+for\s+a/c\s+(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif "between" in low:
                    match = re.search(
                        r"between\s+(\d{2}-[A-Za-z]{3}-\d{4})\s+and\s+(\d{2}-[A-Za-z]{3}-\d{4})",
                        line, re.IGNORECASE,
                    )
                    if match:
                        data["statement_from"] = match.group(1)
                        data["statement_to"] = match.group(2)

            except Exception as field_exc:
                logger.debug("[CBI] Error parsing line '%s': %s", line, field_exc)

        # --- First HTML table: Client Info ---
        client_table_match = re.search(r"<table>.*?</table>", md_text, re.DOTALL | re.IGNORECASE)
        if client_table_match:
            html = client_table_match.group(0)
            rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL | re.IGNORECASE)
            for row in rows:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
                if len(cells) >= 2:
                    try:
                        key = clean(cells[0]).lower()
                        value = clean(cells[1])

                        if "client code name" in key:
                            data["client_code"] = value
                        elif "address" in key:
                            address_keywords = [
                                "plot", "khati", "khatib", "nagar", "road",
                                "lane", "street", "flat", "building", "tower",
                            ]
                            parts = value.split()
                            name_parts, addr_parts = [], []
                            found_addr = False
                            for part in parts:
                                has_number = any(c.isdigit() for c in part)
                                is_addr_kw = any(kw in part.lower() for kw in address_keywords)
                                if not found_addr and (has_number or is_addr_kw):
                                    found_addr = True
                                (addr_parts if found_addr else name_parts).append(part)
                            if name_parts:
                                data["name"] = " ".join(name_parts)
                            if addr_parts:
                                data["customer_address"] = " ".join(addr_parts)
                        elif "phone" in key:
                            data["phone"] = value

                    except Exception as cell_exc:
                        logger.debug("[CBI] Error parsing client table cell: %s", cell_exc)

        # --- Second HTML table: Branch Info ---
        all_tables_html = re.findall(r"<table>.*?</table>", md_text, re.DOTALL | re.IGNORECASE)
        if len(all_tables_html) > 1:
            branch_html = all_tables_html[1]
            rows = re.findall(r"<tr[^>]*>.*?</tr>", branch_html, re.DOTALL | re.IGNORECASE)
            in_branch_address = False
            branch_addr_lines = []

            for row in rows:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
                if not cells:
                    continue

                try:
                    if len(cells) >= 2:
                        key = clean(cells[0]).lower()
                        value = clean(cells[1])

                        if "branch code" in key:
                            match = re.search(r"(\d+)", value)
                            if match:
                                data["branch_code"] = match.group(1)
                            # Key may be "Branch Code Branch Name" — name comes from next Address row
                            in_branch_address = False
                        elif "address" in key:
                            # First value under Address is the branch name
                            if not data.get("branch_name") and value:
                                data["branch_name"] = value
                            in_branch_address = True
                            branch_addr_lines = []
                        elif "ifsc" in key:
                            match = re.search(r"CBIN\d+", value, re.IGNORECASE)
                            if match:
                                data["ifsc"] = match.group(0).upper()
                            in_branch_address = False

                    elif len(cells) == 1 and in_branch_address:
                        # Continuation rows under a rowspan — no rowspan attr on these rows
                        branch_addr_lines.append(clean(cells[0]))

                except Exception as cell_exc:
                    logger.debug("[CBI] Error parsing branch table cell: %s", cell_exc)

            if branch_addr_lines:
                data["branch_address"] = " ".join(branch_addr_lines)

        # --- Fallback: parsed table objects ---
        tables = extract_tables(md_text)
        if tables and not data.get("client_code"):
            for row in tables[0]:
                if len(row) >= 2:
                    key = row[0].lower()
                    value = row[1]
                    if "client code" in key:
                        data["client_code"] = value
                    elif "phone" in key:
                        data["phone"] = value

        if len(tables) > 1 and not data.get("branch_code"):
            for row in tables[1]:
                if len(row) >= 2:
                    key, value = row[0].lower(), row[1]
                    if "branch code" in key:
                        match = re.search(r"(\d+)", value)
                        if match:
                            data["branch_code"] = match.group(1)
                    elif "branch name" in key and not data.get("branch_name"):
                        data["branch_name"] = value
                    elif "ifsc" in key and not data.get("ifsc"):
                        match = re.search(r"CBIN\d+", value, re.IGNORECASE)
                        if match:
                            data["ifsc"] = match.group(0).upper()

        # Only keep transaction tables (has date + particulars columns)
        transaction_tables = [
            t for t in tables
            if t and len(t[0]) >= 4
            and any("date" in h.lower() for h in t[0])
            and any("particulars" in h.lower() or "description" in h.lower() for h in t[0])
        ]

    except Exception as exc:
        logger.error("[CBI] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
