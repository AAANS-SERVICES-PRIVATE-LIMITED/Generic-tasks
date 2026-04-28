import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a PNB (Punjab National Bank) statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[PNB] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        in_branch_address = False
        in_customer_address = False
        branch_address_lines: list[str] = []
        customer_address_lines: list[str] = []

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                if "branch name" in low:
                    data["branch"] = line.split(":")[-1].strip()

                elif "branch address" in low:
                    in_branch_address = True
                    addr_part = line.split(":")[-1].strip()
                    if addr_part:
                        branch_address_lines.append(addr_part)

                elif "customer name" in low:
                    in_branch_address = False
                    data["name"] = line.split(":")[-1].strip()

                elif "customer address" in low:
                    in_customer_address = True
                    in_branch_address = False
                    addr_part = line.split(":")[-1].strip()
                    if addr_part:
                        customer_address_lines.append(addr_part)

                elif "city" in low and ":" in line:
                    city_val = line.split(":")[-1].strip()
                    if in_branch_address and "customer" not in low:
                        data["branch_city"] = city_val
                        in_branch_address = False
                    elif in_customer_address:
                        data["customer_city"] = city_val

                elif "ifsc code" in low:
                    in_branch_address = False
                    data["ifsc"] = line.split(":")[-1].strip()

                elif "pin" in low and ":" in line:
                    pin_val = line.split(":")[-1].strip()
                    if pin_val:
                        data["pin"] = pin_val
                    if in_customer_address:
                        in_customer_address = False

                elif "ckyc number" in low or "ckyc" in low:
                    data["ckyc"] = line.split(":")[-1].strip()

                elif "nominee" in low and ":" in line:
                    data["nominee"] = line.split(":")[-1].strip()

                elif "statement of account" in low:
                    match = re.search(r"account[:\s]+(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)
                    period_match = re.search(
                        r"period[:\s]+(\d{2}/\d{2}/\d{4})\s+to\s+(\d{2}/\d{2}/\d{4})",
                        line, re.IGNORECASE,
                    )
                    if period_match:
                        data["statement_from"] = period_match.group(1)
                        data["statement_to"] = period_match.group(2)

                elif in_branch_address and ":" not in line and line.strip():
                    branch_address_lines.append(line.strip())

                elif in_customer_address and ":" not in line and line.strip():
                    customer_address_lines.append(line.strip())

            except Exception as field_exc:
                logger.debug("[PNB] Error parsing line '%s': %s", line, field_exc)

        if branch_address_lines:
            data["branch_address"] = " ".join(branch_address_lines)
        if customer_address_lines:
            data["customer_address"] = " ".join(customer_address_lines)

        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[PNB] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
