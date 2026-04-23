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

    # UCO specific extraction - simple line-by-line format
    address_lines = []
    in_address = False

    for i, line in enumerate(lines):
        low = line.lower()

        # Statement header with account number
        if "statement for a/c" in low:
            match = re.search(r'statement\s+for\s+a/c\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)
            # Statement period
            match = re.search(r'between\s+([\d-]+)\s*and\s+([\d-]+)', line, re.IGNORECASE)
            if match:
                data["statement_from"] = match.group(1)
                data["statement_to"] = match.group(2)

        # Client Code
        elif "client code" in low:
            match = re.search(r'client\s*code\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["client_code"] = match.group(1)
            else:
                if i + 1 < len(lines) and lines[i+1].strip().isdigit():
                    data["client_code"] = lines[i+1].strip()

        # Name
        elif "name" in low and "branch" not in low:
            match = re.search(r'name\s*(.+)', line, re.IGNORECASE)
            if match:
                data["name"] = match.group(1).strip()
            else:
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and not next_line.lower().startswith('branch'):
                        data["name"] = next_line

        # Branch Code
        elif "branch code" in low:
            match = re.search(r'branch\s*code\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["branch_code"] = match.group(1)
            else:
                if i + 1 < len(lines) and lines[i+1].strip().isdigit():
                    data["branch_code"] = lines[i+1].strip()

        # IFSC Code
        elif "ifsc" in low:
            match = re.search(r'ifsc\s*code\s*(UCBA\d+)', line, re.IGNORECASE)
            if match:
                data["ifsc"] = match.group(1).upper()
            else:
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if 'UCBA' in next_line.upper():
                        data["ifsc"] = next_line

        # Address - multi-line format
        elif "address" in low:
            in_address = True
            # Check if there's content on same line after "Address"
            match = re.search(r'address\s*(.+)', line, re.IGNORECASE)
            if match and match.group(1).strip():
                address_lines.append(match.group(1).strip())
            else:
                # Get next line as address start
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    # Check it's not a label
                    if not any(x in next_line.lower() for x in ['branch', 'phone', 'ifsc', 'client']):
                        address_lines.append(next_line)

        elif in_address:
            # Continue collecting address lines until we hit a label
            if any(x in low for x in ['branch name', 'phone', 'ifsc', 'client', 'branch code']):
                in_address = False
            elif line.strip().isdigit() and len(line.strip()) == 6:
                # PIN code
                data["pin"] = line.strip()
                in_address = False
            else:
                # This is an address line
                address_lines.append(line)

        # Branch Name
        elif "branch name" in low:
            match = re.search(r'branch\s*name\s*(.+)', line, re.IGNORECASE)
            if match:
                data["branch_name"] = match.group(1).strip()
            else:
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and not next_line.lower().startswith('address'):
                        data["branch_name"] = next_line

        # Phone
        elif "phone" in low:
            match = re.search(r'phone\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["phone"] = match.group(1)
            else:
                if i + 1 < len(lines) and lines[i+1].strip().isdigit():
                    data["phone"] = lines[i+1].strip()

        # PIN code detection (6 digits)
        elif line.strip().isdigit() and len(line.strip()) == 6 and not data.get("pin"):
            data["pin"] = line.strip()

    # Build address from collected lines
    if address_lines:
        data["address"] = ", ".join(address_lines)

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
