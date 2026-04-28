import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a YES Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[YES] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # Extract name (lines after IFSC, before address)
        name_parts = []
        in_name_section = False
        for i, line in enumerate(lines):
            low = line.lower()

            # Start capturing name after IFSC
            if "ifsc" in low and "code" in low:
                in_name_section = True
                continue

            # Stop at address (contains numbers like "12/2" or pincode)
            if in_name_section:
                # Check if line looks like address (starts with numbers or has pattern like "12/2")
                if re.match(r'^\d+[/\s]', line.strip()):
                    break
                if line.strip() and len(line.strip()) > 2 and not any(char.isdigit() for char in line):
                    name_parts.append(line.strip())

        if name_parts:
            data["name"] = " ".join(name_parts)

        # Extract address (lines that look like address - start with numbers or contain pincode)
        address_parts = []
        for line in lines:
            low = line.lower()

            # Skip lines that are clearly metadata
            if any(keyword in low for keyword in ["account", "ifsc", "branch", "yes bank"]):
                continue

            # Check if line looks like address (starts with numbers or is pincode)
            if re.match(r'^\d+[/\s]', line.strip()) or (line.strip().isdigit() and len(line.strip()) == 6):
                address_parts.append(line.strip())

        if address_parts:
            data["address"] = " ".join(address_parts)

        # Extract other metadata from text lines
        for line in lines:
            low = line.lower()

            try:
                if "account number" in low:
                    match = re.search(r"account\s*number\s*[:]\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif "ifsc" in low and "code" in low:
                    match = re.search(r"ifsc\s*code\s*[:]\s*(\w+)", line, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(1)

                elif "branch" in low and ":" in line:
                    match = re.search(r"branch\s*[:]\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch"] = match.group(1).strip()

            except Exception as field_exc:
                logger.debug("[YES] Error parsing line '%s': %s", line, field_exc)

        # Extract transaction tables
        tables = extract_tables(md_text)
        transaction_tables = tables if tables else []

    except Exception as exc:
        logger.error("[YES] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
