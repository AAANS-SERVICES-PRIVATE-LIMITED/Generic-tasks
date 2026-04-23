import re
from html.parser import HTMLParser


def clean(text):
    return text.strip()


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
            self.current_table = []
        elif tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif tag in ('td', 'th'):
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
            if self.current_table:
                self.tables.append(self.current_table)
        elif tag == 'tr':
            self.in_row = False
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag in ('td', 'th'):
            self.in_cell = False
            cell_text = ''.join(self.current_cell).strip()
            self.current_row.append(cell_text)

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)


def extract_tables(md_text):
    """Extract HTML tables from markdown text."""
    table_pattern = r'<table>.*?</table>'
    table_matches = re.findall(table_pattern, md_text, re.DOTALL | re.IGNORECASE)

    all_tables = []
    for table_html in table_matches:
        parser = TableParser()
        parser.feed(table_html)
        if parser.tables:
            all_tables.extend(parser.tables)

    return all_tables


def table_to_markdown(table):
    """Convert table data to markdown table format."""
    if not table or len(table) == 0:
        return ""

    md_lines = []
    header = table[0]
    md_lines.append("| " + " | ".join(str(cell) for cell in header) + " |")
    md_lines.append("|" + "|".join(" --- " for _ in header) + "|")
    for row in table[1:]:
        md_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return "\n".join(md_lines)


def extract(bank_name, md_text, ocr_text=None):
    lines = [clean(l) for l in md_text.split("\n") if l.strip()]

    data = {}
    data["bank"] = bank_name

    # PSB specific extraction from text lines
    for i, line in enumerate(lines):
        low = line.lower()

        # Phone
        if "phone:" in low:
            match = re.search(r'phone[:\s]+([\d\-]+)', line, re.IGNORECASE)
            if match:
                data["phone"] = match.group(1)

        # Website
        elif "website:" in low:
            match = re.search(r'website[:\s]+(\S+)', line, re.IGNORECASE)
            if match:
                data["website"] = match.group(1)

        # Account number (if found in text)
        elif "account" in low and any(c.isdigit() for c in line):
            match = re.search(r'account\s*(?:number|no)[:\s]*(\d+)', line, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)

    # Parse tables for metadata and transactions
    tables = extract_tables(md_text)

    # === FIRST TABLE: Account Summary ===
    if tables and len(tables) > 0:
        summary_table = tables[0]

        # Parse the summary table HTML directly to handle merged fields
        summary_html = re.search(r'<table>.*?</table>', md_text, re.DOTALL | re.IGNORECASE)
        if summary_html:
            html = summary_html.group(0)
            rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL | re.IGNORECASE)

            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if not cells:
                    continue

                # Check for rowspan (merged cells)
                row_text = clean(''.join(cells)).lower()

                # Currency and Overdraft Limit (usually in rowspan cell)
                if 'currency' in row_text and 'inr' in row_text:
                    # Extract currency
                    match = re.search(r'currency[:\s]+(\w+)', row_text, re.IGNORECASE)
                    if match:
                        data["currency"] = match.group(1)
                    # Extract overdraft limit
                    match = re.search(r'limit\s+of\s+overdraft[:\s]+([\d.]+)', row_text, re.IGNORECASE)
                    if match:
                        data["overdraft_limit"] = match.group(1)

                # Date of issue and Name (merged key)
                if len(cells) >= 2:
                    key = clean(cells[0]).lower()
                    value = clean(cells[1])

                    if "date of issue" in key and "name" in key:
                        # Format: "20Feb,2025 AFSHIN HOSSEYNABADI"
                        # Split date and name
                        match = re.search(r'(\d{1,2}[A-Za-z]{3},?\d{4})\s+(.+)', value)
                        if match:
                            data["date_of_issue"] = match.group(1)
                            data["name"] = match.group(2)
                        else:
                            # Try simpler split
                            parts = value.split(None, 1)
                            if len(parts) >= 2:
                                data["date_of_issue"] = parts[0]
                                data["name"] = parts[1]

                    elif "address" in key:
                        # Address might be in next row (empty cell case)
                        if value:
                            data["address"] = value

                # Handle address continuation (address in second cell of row with empty first cell)
                if len(cells) == 2:
                    first_cell = clean(cells[0])
                    second_cell = clean(cells[1])
                    if not first_cell and second_cell and ',' in second_cell:
                        # This is likely the address
                        data["address"] = second_cell

        # Also try parsed table as fallback
        for row in summary_table:
            row_text = ' '.join(row).lower()

            # Look for merged date/name field
            for cell in row:
                # Pattern: date followed by name (e.g., "20Feb,2025 AFSHIN HOSSEYNABADI")
                match = re.search(r'(\d{1,2}[A-Za-z]{3},?\d{4})\s+([A-Za-z\s]+)', cell)
                if match and not data.get("date_of_issue"):
                    potential_name = match.group(2).strip()
                    # Validate it looks like a name (contains only letters/spaces)
                    if potential_name.replace(' ', '').isalpha():
                        data["date_of_issue"] = match.group(1)
                        data["name"] = potential_name

            # Look for currency
            if 'currency' in row_text and 'inr' in row_text and not data.get("currency"):
                data["currency"] = "INR"
                # Try to get overdraft limit
                match = re.search(r'overdraft[:\s]+([\d.]+)', row_text, re.IGNORECASE)
                if match:
                    data["overdraft_limit"] = match.group(1)

            # Look for address
            for cell in row:
                if ',' in cell and not data.get("address"):
                    # Check if it looks like an address (has city/state pattern)
                    if any(x in cell.lower() for x in ['maharashtra', 'india', 'nagar', 'gaon', 'road']):
                        data["address"] = cell

    # === TRANSACTION TABLE ===
    transaction_tables = []
    if len(tables) > 1:
        for table in tables[1:]:
            if table and len(table) > 0:
                header = [h.lower() for h in table[0]]
                # Check if it's a transaction table
                if any('date' in h for h in header) and any(h in ' '.join(header) for h in ['description', 'particulars', 'withdrawals', 'deposits', 'balance']):
                    transaction_tables.append(table)

    # Print tables in markdown format (only transaction tables)
    for i, table in enumerate(transaction_tables, 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": transaction_tables
    }
