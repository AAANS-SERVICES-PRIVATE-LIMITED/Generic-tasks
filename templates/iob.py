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

    # IOB specific extraction
    # First line contains name and address: "John Citizen, 19Ashoka Road..."
    if lines:
        first_line = lines[0]
        # Extract name (everything before the first comma)
        if "," in first_line:
            name_part = first_line.split(",")[0].strip()
            data["name"] = name_part

    for i, line in enumerate(lines):
        low = line.lower()

        # Opening Balance
        if "opening balance" in low:
            match = re.search(r'opening\s+balance[:\s]+([\d.,]+)', line, re.IGNORECASE)
            if match:
                data["opening_balance"] = match.group(1)

        # Withdrawals
        elif "withdrawals" in low:
            match = re.search(r'withdrawals[:\s]+([\d.,]+)', line, re.IGNORECASE)
            if match:
                data["total_withdrawals"] = match.group(1)

        # Deposits
        elif "deposits" in low and "closing" not in low:
            match = re.search(r'deposits[:\s]+([\d.,]+)', line, re.IGNORECASE)
            if match:
                data["total_deposits"] = match.group(1)

        # Closing Balance
        elif "closing balance" in low:
            match = re.search(r'closing\s+balance[:\s]+([\d.,]+)', line, re.IGNORECASE)
            if match:
                data["closing_balance"] = match.group(1)
            # Also try to get date from "Closing Balance on Apr 18, 2021"
            match_date = re.search(r'closing\s+balance\s+on\s+([A-Za-z]+\s+\d{1,2},\s*\d{4})', line, re.IGNORECASE)
            if match_date:
                data["closing_date"] = match_date.group(1)

        # Account number patterns (if present)
        elif re.search(r'account\s*(?:number|no)[:\s]+(\d+)', low):
            match = re.search(r'account\s*(?:number|no)[:\s]+(\d+)', line, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)

        # Statement date patterns
        elif re.search(r'statement\s+(?:date|period)', low):
            match = re.search(r'statement\s+(?:date|period)[:\s]+(.+)', line, re.IGNORECASE)
            if match:
                data["statement_date"] = match.group(1).strip()

    # Extract tables
    tables = extract_tables(md_text)

    # First table often contains summary info
    if tables and len(tables) > 0:
        first_table = tables[0]
        # Parse cells for opening/closing balance info
        for row in first_table:
            row_text = " ".join(row).lower()
            if "opening balance" in row_text and "opening_balance" not in data:
                # Try to find number pattern
                match = re.search(r'([\d.,]+)\s*(?:INR|Rs\.?)', " ".join(row), re.IGNORECASE)
                if match:
                    data["opening_balance"] = match.group(1)
            if "withdrawals" in row_text and "total_withdrawals" not in data:
                match = re.search(r'([\d.,]+)\s*(?:INR|Rs\.?)', " ".join(row), re.IGNORECASE)
                if match:
                    data["total_withdrawals"] = match.group(1)
            if "deposits" in row_text and "total_deposits" not in data:
                match = re.search(r'([\d.,]+)\s*(?:INR|Rs\.?)', " ".join(row), re.IGNORECASE)
                if match:
                    data["total_deposits"] = match.group(1)

    # Print tables in markdown format
    for i, table in enumerate(tables, 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": tables
    }
