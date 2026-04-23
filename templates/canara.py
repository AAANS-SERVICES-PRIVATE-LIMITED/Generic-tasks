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

    # Canara specific - name is first line (all caps company name)
    for line in lines:
        if line.isupper() and len(line.split()) >= 2 and not line.startswith("##"):
            data["name"] = line
            break

    # Extract from metadata table (first table usually contains account info)
    tables = extract_tables(md_text)

    # First table typically has account metadata in key-value pairs
    if tables and len(tables) > 0:
        meta_table = tables[0]
        for row in meta_table:
            if len(row) >= 2:
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
                    # Extract period: "From 01 Dec 2022 To 31 Mar 2023"
                    match = re.search(r'from\s+(.+?)\s+to\s+(.+)', value.lower())
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
                    # Remove currency prefix and extract number
                    balance = re.sub(r'RS\.?\s*', '', value, flags=re.IGNORECASE).strip()
                    data["opening_balance"] = balance
                elif "closing balance" in key:
                    balance = re.sub(r'RS\.?\s*', '', value, flags=re.IGNORECASE).strip()
                    data["closing_balance"] = balance

    # Address is multi-line before first table
    address_lines = []
    capture = False
    for line in lines:
        if "account statement" in line.lower():
            capture = True
            continue
        if "<table>" in line.lower() or line.startswith("|"):
            break
        if capture and line and not line.startswith("##"):
            address_lines.append(line)

    if address_lines:
        data["address"] = " ".join(address_lines[:5])  # Limit address lines

    # Print tables in markdown format (skip first metadata table for transactions)
    transaction_tables = tables[1:] if len(tables) > 1 else []
    for i, table in enumerate(transaction_tables, 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": transaction_tables
    }
