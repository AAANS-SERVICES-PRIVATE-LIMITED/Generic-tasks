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
    data = {}
    data["bank"] = bank_name

    # BOM stores everything in tables, parse the first (customer details) table
    tables = extract_tables(md_text)

    if tables and len(tables) > 0:
        # First table has customer and account details
        customer_table = tables[0]

        for row in customer_table:
            if len(row) >= 2:
                left_cell = row[0].lower()
                right_cell = row[1].lower()

                # Left column - customer details
                if "name:" in left_cell:
                    data["name"] = row[0].split(":")[-1].strip()
                elif "address:" in left_cell:
                    data["address"] = row[0].split(":")[-1].strip()
                elif "mobile:" in left_cell:
                    data["mobile"] = row[0].split(":")[-1].strip()
                elif "email" in left_cell:
                    data["email"] = row[0].split(":")[-1].strip()
                elif "date of birth" in left_cell:
                    data["dob"] = row[0].split(":")[-1].strip()
                elif "cif number" in left_cell:
                    data["cif"] = row[0].split(":")[-1].strip()

                # Right column - branch/account details
                if "ifsc" in right_cell:
                    data["ifsc"] = row[1].split(":")[-1].strip()
                elif "branch name" in right_cell:
                    data["branch"] = row[1].split(":")[-1].strip()
                elif "account no" in right_cell:
                    data["account_number"] = row[1].split(":")[-1].strip()
                elif "account type" in right_cell:
                    data["account_type"] = row[1].split(":")[-1].strip()
                elif "total balance" in right_cell:
                    data["total_balance"] = row[1].split(":")[-1].strip()

    # Print transaction tables (skip first customer table)
    for i, table in enumerate(tables[1:] if len(tables) > 1 else [], 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": tables
    }
