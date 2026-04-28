import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a Canara Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[Canara] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        # Name — first ALL-CAPS line with ≥2 words
        for line in lines:
            try:
                if line.isupper() and len(line.split()) >= 2 and not line.startswith("##"):
                    data["name"] = line
                    break
            except Exception:
                pass

        tables = extract_tables(md_text)

        # First table: account metadata key-value pairs
        if tables:
            for row in tables[0]:
                if len(row) >= 2:
                    try:
                        key = row[0].lower()
                        value = row[1]

                        if "customer id" in key:
                            data["customer_id"] = value
                        elif "account number" in key:
                            data["account_number"] = value
                        elif "ifsc" in key:
                            data["ifsc"] = value
                        elif "micr" in key:
                            data["micr"] = value
                        elif "account holders name" in key:
                            data["name"] = value
                        elif "branch name" in key:
                            data["branch"] = value
                        elif "searched by" in key:
                            match = re.search(r"from\s+(.+?)\s+to\s+(.+)", value, re.IGNORECASE)
                            if match:
                                data["statement_from"] = match.group(1).strip()
                                data["statement_to"] = match.group(2).strip()
                            else:
                                data["statement_period"] = value
                        elif "account currency" in key:
                            data["currency"] = value
                        elif "product name" in key:
                            data["product"] = value
                        elif "opening balance" in key:
                            data["opening_balance"] = re.sub(r"RS\.?\s*", "", value, flags=re.IGNORECASE).strip()
                        elif "closing balance" in key:
                            data["closing_balance"] = re.sub(r"RS\.?\s*", "", value, flags=re.IGNORECASE).strip()

                    except Exception as cell_exc:
                        logger.debug("[Canara] Error parsing metadata row: %s", cell_exc)

        # Address from text between "account statement" header and first table
        address_lines: list[str] = []
        capture = False
        for line in lines:
            try:
                if "account statement" in line.lower():
                    capture = True
                    continue
                if "<table>" in line.lower() or line.startswith("|"):
                    break
                if capture and line and not line.startswith("##"):
                    address_lines.append(line)
            except Exception:
                pass

        if address_lines:
            data["address"] = " ".join(address_lines[:5])

        transaction_tables = tables[1:] if len(tables) > 1 else []

    except Exception as exc:
        logger.error("[Canara] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
