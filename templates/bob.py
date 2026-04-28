import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a BOB (Bank of Baroda) bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[BOB] md_text is empty; will try OCR-only extraction.")

    try:
        lines = [clean(l) for l in (md_text or "").split("\n") if l.strip()]

        # Name is before "Customer ID" on the first line
        if lines:
            match = re.search(r"^(.+?)\s+customer\s+id\s*[:\-]?\s*", lines[0], re.IGNORECASE)
            if match:
                data["name"] = match.group(1).strip()

        for line in lines:
            low = line.lower()

            try:
                if "customer id" in low:
                    match = re.search(r"customer\s*id[:\s]+([A-Za-z0-9X]+)", line, re.IGNORECASE)
                    if match:
                        data["customer_id"] = match.group(1)

                elif "registered address" in low and not data.get("address"):
                    # e.g. "...Registered Address: Jai Ambe Chawl...PIN: 400606"
                    match = re.search(r"registered\s*address[:\s]+(.+?)(?:\s+pin[:\s]|$)", line, re.IGNORECASE)
                    if match:
                        data["address"] = match.group(1).strip()
                    pin_match = re.search(r"pin[:\s]+(\d{6})", line, re.IGNORECASE)
                    if pin_match:
                        data["pin"] = pin_match.group(1)

                elif "account no" in low:
                    match = re.search(r"account\s*no[-:\s]+(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

                elif ("branch" in low or "ifsc" in low or "barb" in low) and not data.get("branch"):
                    # e.g. "Branch-DAHIYAWAN Ifsc Code-BARBODAHIYA MICR Code-211015214"
                    branch_match = re.search(r"branch[-:\s]+([A-Za-z]+)", line, re.IGNORECASE)
                    if branch_match:
                        data["branch"] = branch_match.group(1).strip()
                    if not data.get("ifsc"):
                        ifsc_match = re.search(r"ifsc\s*code[-:\s]+([A-Z0-9]+)", line, re.IGNORECASE)
                        if ifsc_match:
                            data["ifsc"] = ifsc_match.group(1).upper()
                        else:
                            barb_match = re.search(r"\bBARB[A-Z0-9]{6,}\b", line, re.IGNORECASE)
                            if barb_match:
                                data["ifsc"] = barb_match.group(0).upper()
                    if not data.get("micr"):
                        micr_match = re.search(r"micr\s*code[-:\s]*(\d+)", line, re.IGNORECASE)
                        if micr_match:
                            data["micr"] = micr_match.group(1)

                elif "detailed statement" in low and "between" in low:
                    match = re.search(
                        r"between\s+(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})",
                        line, re.IGNORECASE,
                    )
                    if match:
                        data["statement_from"] = match.group(1)
                        data["statement_to"] = match.group(2)

            except Exception as field_exc:
                logger.debug("[BOB] Error parsing line '%s': %s", line, field_exc)

        # --- OCR fallback for grey-box data that MinerU misses ---
        if ocr_text:
            ocr_lines = [clean(l) for l in ocr_text.split("\n") if l.strip()]
            logger.debug("[BOB] Scanning %d OCR lines for grey-box fields.", len(ocr_lines))

            for line in ocr_lines:
                low = line.lower()

                try:
                    if ("branch-" in low or "branch:" in low) and not data.get("branch"):
                        match = re.search(r"branch[-:\s]+([A-Za-z]+)", line, re.IGNORECASE)
                        if match:
                            data["branch"] = match.group(1)
                            logger.debug("[BOB] branch from OCR: %s", data["branch"])

                    if ("barb" in low or "ifsc" in low or "baroda" in low) and not data.get("ifsc"):
                        match = re.search(r"barb[a-z0-9]+", line, re.IGNORECASE)
                        if match:
                            data["ifsc"] = match.group(0).upper()
                            logger.debug("[BOB] ifsc from OCR: %s", data["ifsc"])
                        match2 = re.search(r"ifsc\s*code[:\-\s]+([a-z0-9]+)", line, re.IGNORECASE)
                        if match2 and not data.get("ifsc"):
                            data["ifsc"] = match2.group(1).upper()
                            logger.debug("[BOB] ifsc (label) from OCR: %s", data["ifsc"])

                    if "micr" in low and not data.get("micr"):
                        match = re.search(r"micr\s*code[-:\s]*(\d+)", line, re.IGNORECASE)
                        if match:
                            data["micr"] = match.group(1)
                        else:
                            match = re.search(r"micr.*?(\d{9})", line, re.IGNORECASE)
                            if match:
                                data["micr"] = match.group(1)
                        if data.get("micr"):
                            logger.debug("[BOB] micr from OCR: %s", data["micr"])

                except Exception as field_exc:
                    logger.debug("[BOB] Error parsing OCR line '%s': %s", line, field_exc)

        tables = extract_tables(md_text or "")

    except Exception as exc:
        logger.error("[BOB] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": tables}
