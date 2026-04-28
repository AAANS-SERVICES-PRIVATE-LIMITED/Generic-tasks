import re
import logging
from .base import clean, extract_tables, table_to_markdown

logger = logging.getLogger(__name__)


def extract(bank_name: str, md_text: str, ocr_text: str = None) -> dict:
    """Extract metadata and transactions from a PSB (Punjab & Sind Bank) statement."""
    data: dict = {"bank": bank_name}

    if not md_text:
        logger.warning("[PSB] md_text is empty; skipping extraction.")
        return {"metadata": data, "tables": []}

    try:
        lines = [clean(l) for l in md_text.split("\n") if l.strip()]

        for i, line in enumerate(lines):
            low = line.lower()

            try:
                if "phone:" in low:
                    match = re.search(r"phone[:\s]+([\d\-]+)", line, re.IGNORECASE)
                    if match:
                        data["phone"] = match.group(1)

                elif "website:" in low:
                    match = re.search(r"website[:\s]+(\S+)", line, re.IGNORECASE)
                    if match:
                        data["website"] = match.group(1)

                elif "account" in low and any(c.isdigit() for c in line):
                    match = re.search(r"account\s*(?:number|no)[:\s]*(\d+)", line, re.IGNORECASE)
                    if match:
                        data["account_number"] = match.group(1)

            except Exception as field_exc:
                logger.debug("[PSB] Error parsing line '%s': %s", line, field_exc)

        # --- Account Summary Table ---
        tables = extract_tables(md_text)

        summary_html = re.search(r"<table>.*?</table>", md_text, re.DOTALL | re.IGNORECASE)
        if summary_html:
            html = summary_html.group(0)
            rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL | re.IGNORECASE)

            for row in rows:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
                if not cells:
                    continue

                try:
                    row_text = clean("".join(cells)).lower()

                    if "currency" in row_text and "inr" in row_text:
                        match = re.search(r"currency[:\s]+(\w+)", row_text, re.IGNORECASE)
                        if match:
                            data["currency"] = match.group(1).upper()
                        match2 = re.search(r"limit\s+of\s+overdraft[:\s]+([\d.]+)", row_text, re.IGNORECASE)
                        if match2:
                            data["overdraft_limit"] = match2.group(1)

                    if len(cells) >= 2:
                        key = clean(cells[0]).lower()
                        value = clean(cells[1])

                        if "date of issue" in key and "name" in key:
                            match = re.search(r"(\d{1,2}[A-Za-z]{3},?\d{4})\s+(.+)", value)
                            if match:
                                data["date_of_issue"] = match.group(1)
                                data["name"] = match.group(2)
                            else:
                                parts = value.split(None, 1)
                                if len(parts) >= 2:
                                    data["date_of_issue"] = parts[0]
                                    data["name"] = parts[1]
                        elif "address" in key and value:
                            data["address"] = value

                    if len(cells) == 2:
                        first_cell = clean(cells[0])
                        second_cell = clean(cells[1])
                        if not first_cell and second_cell and "," in second_cell:
                            data.setdefault("address", second_cell)

                except Exception as cell_exc:
                    logger.debug("[PSB] Error parsing summary table cell: %s", cell_exc)

        # Fallback: parsed table
        if tables and not data.get("name"):
            for row in tables[0]:
                for cell in row:
                    try:
                        match = re.search(r"(\d{1,2}[A-Za-z]{3},?\d{4})\s+([A-Za-z\s]+)", cell)
                        if match:
                            potential_name = match.group(2).strip()
                            if potential_name.replace(" ", "").isalpha():
                                data["date_of_issue"] = match.group(1)
                                data["name"] = potential_name
                    except Exception:
                        pass

            row_texts = [" ".join(r).lower() for r in tables[0]]
            if any("currency" in rt and "inr" in rt for rt in row_texts) and not data.get("currency"):
                data["currency"] = "INR"

        # --- Transaction tables ---
        transaction_tables = [
            t for t in tables[1:]
            if t and len(t) > 0
            and any("date" in h.lower() for h in t[0])
            and any(
                h in " ".join(t[0]).lower()
                for h in ["description", "particulars", "withdrawals", "deposits", "balance"]
            )
        ]

    except Exception as exc:
        logger.error("[PSB] Extraction failed: %s", exc, exc_info=True)
        return {"metadata": data, "tables": []}

    return {"metadata": data, "tables": transaction_tables}
