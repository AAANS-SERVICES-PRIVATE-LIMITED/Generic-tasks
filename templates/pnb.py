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

    # PNB specific - colon separated fields
    in_branch_address = False
    in_customer_address = False
    branch_address_lines = []
    customer_address_lines = []

    for i, line in enumerate(lines):
        low = line.lower()

        if "branch name" in low:
            data["branch"] = line.split(":")[-1].strip()

        elif "branch address" in low:
            in_branch_address = True
            addr_part = line.split(":")[-1].strip()
            if addr_part:
                branch_address_lines.append(addr_part)

        elif "customer name" in low:
            in_branch_address = False  # End branch section
            data["name"] = line.split(":")[-1].strip()

        elif "customer address" in low:
            in_customer_address = True
            in_branch_address = False
            addr_part = line.split(":")[-1].strip()
            if addr_part:
                customer_address_lines.append(addr_part)

        elif "city" in low and ":" in line:
            city_val = line.split(":")[-1].strip()
            if in_branch_address and "customer" not in low:
                data["branch_city"] = city_val
                in_branch_address = False
            elif in_customer_address:
                data["customer_city"] = city_val

        elif "ifsc code" in low:
            in_branch_address = False
            data["ifsc"] = line.split(":")[-1].strip()

        elif "pin" in low and ":" in line:
            pin_val = line.split(":")[-1].strip()
            if pin_val:
                data["pin"] = pin_val
            if in_customer_address:
                in_customer_address = False

        elif "ckyc number" in low or "ckyc" in low:
            val = line.split(":")[-1].strip()
            data["ckyc"] = val if val else ""

        elif "nominee" in low and ":" in line:
            val = line.split(":")[-1].strip()
            data["nominee"] = val if val else ""

        elif "statement of account" in low:
            # Extract account number: "Statement of Account:0979000100548481"
            match = re.search(r'account[:\s]+(\d+)', line.lower())
            if match:
                data["account_number"] = match.group(1)
            # Extract period: "For Period: 01/03/2024 to 20/08/2024"
            period_match = re.search(r'period[:\s]+(\d{2}/\d{2}/\d{4})\s+to\s+(\d{2}/\d{2}/\d{4})', line.lower())
            if period_match:
                data["statement_from"] = period_match.group(1)
                data["statement_to"] = period_match.group(2)

        elif in_branch_address and ":" not in line and line.strip():
            # Continuation of branch address
            branch_address_lines.append(line.strip())
        elif in_customer_address and ":" not in line and line.strip():
            # Continuation of customer address
            customer_address_lines.append(line.strip())

    if branch_address_lines:
        data["branch_address"] = " ".join(branch_address_lines)
    if customer_address_lines:
        data["customer_address"] = " ".join(customer_address_lines)

    # Extract tables
    tables = extract_tables(md_text)

    # Print tables in markdown format
    for i, table in enumerate(tables, 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": tables
    }
