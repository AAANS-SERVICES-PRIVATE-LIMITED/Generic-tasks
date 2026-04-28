import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a UCO Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[UCO] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]
        address_lines: list[str] = []
        in_address = False

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                if "statement for a/c" in low:
                    match = re.search(r"statement\s+for\s+a/c\s*([\d]+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)
                    # Handle missing space: "01-05-2020and 31-07-2020"
                    match2 = re.search(r"between\s+([\d-]+)\s*and\s+([\d-]+)", line, re.IGNORECASE)
                    if match2:
                        data["statement_from"] = match2.group(1)
                        data["statement_to"] = match2.group(2)

                elif "client code" in low:
                    match = re.search(r"client\s*code\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["client_code"] = match.group(1)
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        data["client_code"] = lines[i + 1].strip()

                elif "name" in low and "branch" not in low:
                    match = re.search(r"name\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["name"] = match.group(1).strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.lower().startswith("branch"):
                            data["name"] = next_line

                elif "branch code" in low:
                    # Strip leading OCR apostrophe e.g. "'Branch Code 2025"
                    clean_line = line.lstrip("'\'\u2018\u2019`")
                    match = re.search(r"branch\s*code\s*([\d]+)", clean_line, re.IGNORECASE)
                    if match:
                        data["branch_code"] = match.group(1)
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        data["branch_code"] = lines[i + 1].strip()

                elif "ifsc" in low:
                    # Match any IFSC code (11 chars: 4 alpha + 0 + 6 alphanumeric)
                    match = re.search(r"ifsc\s*(?:code)?\s*([A-Z]{4}0[A-Z0-9]{6})", line, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(1).upper()
                    elif i + 1 < len(lines):
                        next_ifsc = re.search(r"[A-Z]{4}0[A-Z0-9]{6}", lines[i + 1], re.IGNORECASE)
                        if next_ifsc:
                            data["ifsc"] = next_ifsc.group(0).upper()

                elif "address" in low:
                    in_address = True
                    match = re.search(r"address\s*(.+)", line, re.IGNORECASE)
                    if match and match.group(1).strip():
                        address_lines.append(match.group(1).strip())
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not any(x in next_line.lower() for x in ["branch", "phone", "ifsc", "client"]):
                            address_lines.append(next_line)

                elif in_address:
                    if any(x in low for x in ["branch name", "phone", "ifsc", "client", "branch code"]):
                        in_address = False
                    elif line.strip().isdigit() and len(line.strip()) == 6:
                        data["pin"] = line.strip()
                        in_address = False
                    else:
                        address_lines.append(line)

                elif "branch name" in low:
                    match = re.search(r"branch\s*name\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch_name"] = match.group(1).strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.lower().startswith("address"):
                            data["branch_name"] = next_line

                elif "phone" in low:
                    match = re.search(r"phone\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["phone"] = match.group(1)
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        data["phone"] = lines[i + 1].strip()

                elif line.strip().isdigit() and len(line.strip()) == 6 and not data.get("pin"):
                    data["pin"] = line.strip()

            except Exception as field_exc:
                logger.debug("[UCO] Error parsing line '%s': %s", line, field_exc)

        if address_lines:
            data["address"] = ", ".join(address_lines)

        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[UCO] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
