import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an IOB (Indian Overseas Bank) statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[IOB] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # Name and address are on line 0: "Name, address, city, pin"
        if lines:
            first = lines[0]
            if "," in first:
                parts = first.split(",", 1)
                data["name"] = parts[0].strip()
                data["address"] = parts[1].strip()
            else:
                data["name"] = first.strip()

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                if "opening balance" in low:
                    match = re.search(r"opening\s+balance[:\s]+([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["opening_balance"] = match.group(1)

                elif "withdrawals" in low:
                    match = re.search(r"withdrawals[:\s]+([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["total_withdrawals"] = match.group(1)

                elif "deposits" in low and "closing" not in low:
                    match = re.search(r"deposits[:\s]+([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["total_deposits"] = match.group(1)

                elif "closing balance" in low:
                    match = re.search(r"closing\s+balance[:\s]+([\d.,]+)", line, re.IGNORECASE)
                    if match:
                        data["closing_balance"] = match.group(1)
                    match_date = re.search(
                        r"closing\s+balance\s+on\s+([A-Za-z]+\s+\d{1,2},\s*\d{4})",
                        line, re.IGNORECASE,
                    )
                    if match_date:
                        data["closing_date"] = match_date.group(1)

                elif re.search(r"account\s*(?:number|no)[:\s]+(\d+)", low):
                    match = re.search(r"account\s*(?:number|no)[:\s]+(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif re.search(r"statement\s+(?:date|period)", low):
                    match = re.search(r"statement\s+(?:date|period)[:\s]+(.+)", line, re.IGNORECASE)
                    if match:
                        data["statement_date"] = match.group(1).strip()

            except Exception as field_exc:
                logger.debug("[IOB] Error parsing line '%s': %s", line, field_exc)

        tables = extract_tables(md_text)

        # Summary from first table — IOB puts all values in ONE merged cell
        # e.g. "Opening Balance 5.234.0 INR Withdrawals 2.395.67 INR Deposits 2.872.45 INR ..."
        if tables:
            full_text = " ".join(" ".join(row) for row in tables[0])
            try:
                ob = re.search(r"opening\s+balance[\s:]+([\d.,]+)", full_text, re.IGNORECASE)
                if ob:
                    data["opening_balance"] = ob.group(1)
                wd = re.search(r"withdrawals[\s:]+([\d.,]+)", full_text, re.IGNORECASE)
                if wd:
                    data["total_withdrawals"] = wd.group(1)
                dp = re.search(r"deposits[\s:]+([\d.,]+)", full_text, re.IGNORECASE)
                if dp:
                    data["total_deposits"] = dp.group(1)
                cb = re.search(r"closing\s+balance[\s+on]*.+?([\d.,]+)\s*$", full_text, re.IGNORECASE)
                if cb:
                    data["closing_balance"] = cb.group(1)
                cd = re.search(r"closing\s+balance\s+on\s+([A-Za-z]+\s+\d+,\s*\d{4})", full_text, re.IGNORECASE)
                if cd:
                    data["closing_date"] = cd.group(1)
            except Exception as e:
                logger.debug("[IOB] Summary parse error: %s", e)

    except Exception as exc:
        logger.error("[IOB] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    # Skip first table (summary/promotional table), return only transaction tables
    transaction_tables = tables[1:] if len(tables) > 1 else []
    return {"metadata": data, "tables": transaction_tables}
