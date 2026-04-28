import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from an ICICI Bank statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[ICICI] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]
        tables = extract_tables(md_text)

        # --- Extract metadata from text lines ---
        address_parts = []
        in_address = False
        name_extracted = False

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                # Skip image links and empty lines
                if line.startswith("![](") or not line.strip():
                    continue

                # Skip header lines
                if "icici" in low or "khayaa" in low or "bank" in low:
                    continue

                # Name (MR./MRS./MS. followed by name - with or without space)
                if not name_extracted and re.match(r'^(MR|MRS|MS)\.?\s*[A-Z][A-Z\s\.]+$', line.strip().upper()):
                    data["name"] = line.strip()
                    name_extracted = True
                    # Next lines are likely address
                    in_address = True
                    continue

                # Address lines (after name, before "Your Base Branch" or "Visit")
                if in_address and "your base branch" not in low and "visit" not in low:
                    # Stop at non-address content
                    if any(skip in low for skip in ["call", "branch", "contact", "relationship", "kyc", "account", "summary", "cust id", "did you know"]):
                        in_address = False
                    else:
                        # Add to address if it looks like address content
                        if len(line.strip()) > 3 and not line.startswith("MPAN"):
                            address_parts.append(line.strip())

                # Base Branch
                elif "your base branch" in low:
                    match = re.search(r"your base branch:\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["branch"] = match.group(1).strip()
                    in_address = False

                # Customer ID
                elif "cust id" in low or "customer id" in low:
                    match = re.search(r"cust\s*id\s*[:]\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["customer_id"] = match.group(1)
                    # statement_date may be on same line: "...Cust ID: 123 as on March 31, 2020"
                    if "as on" in low:
                        d = re.search(r"as\s+on\s+([A-Za-z]+\s+\d+,\s*\d{4})", line, re.IGNORECASE)
                        if d:
                            data["statement_date"] = d.group(1).strip()
                    in_address = False

                # Statement date
                elif "as on" in low:
                    match = re.search(r"as on\s+([A-Za-z]+\s+\d+,\s*\d{4})", line, re.IGNORECASE)
                    if match:
                        data["statement_date"] = match.group(1).strip()

                # Period from transaction statement line
                elif "for the period" in low or "for theperlod" in low:
                    match = re.search(r"for\s+the\s*(?:period|perlod)\s*(.+)", line, re.IGNORECASE)
                    if match:
                        data["period"] = match.group(1).strip()

                # Account number from statement line (various formats)
                elif "accountnumber" in line.replace(" ", "").lower():
                    # Match account number in formats: "AccountNumber:123456" or "SavingsAccountNumber:123456"
                    match = re.search(r"(?:savings)?account\s*number\s*[:]\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)
                elif "account number" in low:
                    match = re.search(r"account\s*number\s*[:]\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

            except Exception as field_exc:
                logger.debug("[ICICI] Error parsing line '%s': %s", line, field_exc)

        # --- Fallback: Extract account number from full markdown text ---
        if not data.get("account_number"):
            # Search the entire md_text for account number patterns
            match = re.search(r"(?:savings)?account\s*number\s*[:]\s*(\d+)", md_text, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)

        if address_parts:
            data["address"] = " ".join(address_parts)

        # --- Transaction tables (skip first table which is account summary) ---
        transaction_tables = tables[1:] if len(tables) > 1 else tables

    except Exception as exc:
        logger.error("[ICICI] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
