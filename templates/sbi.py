import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an SBI bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[SBI] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        for line in lines:
            low = line.lower()

            try:
                if "account number" in low and ":" in line:
                    data["account_number"] = line.split(":")[-1].strip()

                elif "name" in low and ":" in line and "branch" not in low:
                    data["name"] = line.split(":")[-1].strip()

                elif "ifs code" in low or "ifsc code" in low:
                    data["ifsc"] = line.split(":")[-1].strip()

                elif re.search(r"branch\s*:\s*", line, re.IGNORECASE) and "branchcode" not in low:
                    data["branch"] = line.split(":")[-1].strip()

                elif "currency" in low:
                    data["currency"] = line.split(":")[-1].strip()

                elif "rate of interest" in low:
                    match = re.search(r"(\d+\.?\d*)\s*%", line)
                    data["rate_of_interest"] = (match.group(1) + "%") if match else line.split(":")[-1].strip()

                elif "book balance" in low:
                    data["book_balance"] = line.split(":")[-1].strip()

                elif "available balance" in low and "book" not in low:
                    data["available_balance"] = line.split(":")[-1].strip()

                elif "hold value" in low:
                    data["hold_value"] = line.split(":")[-1].strip()

                elif "uncleared amount" in low:
                    data["uncleared_amount"] = line.split(":")[-1].strip()

                elif "drawing power" in low:
                    data["drawing_power"] = line.split(":")[-1].strip()

                elif "limit sanctioned" in low:
                    data["limit_sanctioned"] = line.split(":")[-1].strip()

                elif re.search(r"balance\s*as\s*on", line, re.IGNORECASE):
                    match = re.search(
                        r"balance\s*as\s*on\s+(.+?)\s*:\s*([-\d,.]+)", line, re.IGNORECASE
                    )
                    if match:
                        data["balance_as_on_date"] = match.group(1).strip()
                        data["balance_as_on_value"] = match.group(2).strip()

                elif re.search(r"corporate\s*address\s*:\s*", line, re.IGNORECASE):
                    addr_parts = [line.split(":")[-1].strip()]
                    idx = lines.index(line)
                    stop_keywords = [
                        "branch", "ifsc", "ifs", "currency", "book balance",
                        "available balance", "rate of interest", "hold value",
                        "uncleared amount", "drawing power", "limit sanctioned",
                    ]
                    for j in range(idx + 1, min(idx + 4, len(lines))):
                        next_line = lines[j]
                        next_low = next_line.lower()
                        if ":" in next_line and any(kw in next_low for kw in stop_keywords):
                            break
                        addr_parts.append(next_line.strip())
                    data["address"] = " ".join(addr_parts).strip()

            except Exception as field_exc:
                logger.debug("[SBI] Error parsing line '%s': %s", line, field_exc)

        tables = extract_tables(md_text)

    except Exception as exc:
        logger.error("[SBI] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
