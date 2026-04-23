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
    """Extract HTML tables from markdown text and return as list of tables."""
    # Find all table tags
    table_pattern = r'<table>.*?</table>'
    table_matches = re.findall(table_pattern, md_text, re.DOTALL | re.IGNORECASE)

    all_tables = []
    for table_html in table_matches:
        parser = TableParser()
        parser.feed(table_html)
        if parser.tables:
            all_tables.extend(parser.tables)

    return all_tables


def print_tables(tables):
    """Print tables in a readable format."""
    if not tables:
        print("No tables found.")
        return

    for i, table in enumerate(tables, 1):
        print(f"\n=== Table {i} ===")
        # Calculate column widths
        col_widths = []
        for row in table:
            for j, cell in enumerate(row):
                if j >= len(col_widths):
                    col_widths.append(0)
                col_widths[j] = max(col_widths[j], len(str(cell)))

        # Print rows
        for row in table:
            formatted_row = " | ".join(
                str(cell).ljust(col_widths[j]) for j, cell in enumerate(row)
            )
            print(formatted_row)
        print("-" * 50)


def table_to_markdown(table):
    """Convert table data to markdown table format."""
    if not table or len(table) == 0:
        return ""

    md_lines = []
    # Header row
    header = table[0]
    md_lines.append("| " + " | ".join(str(cell) for cell in header) + " |")
    # Separator
    md_lines.append("|" + "|".join(" --- " for _ in header) + "|")
    # Data rows
    for row in table[1:]:
        md_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return "\n".join(md_lines)


def extract(bank_name, md_text, ocr_text=None):
    lines = [clean(l) for l in md_text.split("\n") if l.strip()]

    data = {}

    # =========================
    # NAME (line above Joint Holder)
    # =========================
    for i, line in enumerate(lines):
        if "joint holder" in line.lower():
            # Get the line before Joint Holder
            if i > 0:
                name_line = lines[i - 1]
                # Skip markdown headers and empty lines
                if not name_line.startswith("#") and len(name_line.split()) >= 2:
                    data["name"] = name_line
                    break
            break

    # =========================
    # FIELDS
    # =========================
    for line in lines:
        low = line.lower()

        if "customer id" in low:
            data["customer_id"] = line.split(":")[-1].strip()

        elif "micr" in low:
            data["micr_code"] = line.split(":")[-1].strip()

        elif "mobile no" in low and "registered" not in low:
            # Extract only digits for mobile number
            digits = re.sub(r"\D", "", line)
            if digits:
                data["mobile_no"] = digits

        elif "registered mobile" in low:
            data["registered_mobile"] = line.split(":")[-1].strip()

        elif "email" in low:
            data["email"] = line.split(":")[-1].strip()

        elif "ifsc" in low:
            data["ifsc"] = line.split(":")[-1].strip()

        elif "nominee" in low:
            data["nominee"] = line.split(":")[-1].strip()

        elif "pan" in low:
            # PAN pattern: PAN :BQUPK0274M or PAN: BQUPK0274M
            pan_match = re.search(r'[:\s]\s*([A-Z]{5}\d{4}[A-Z])', line)
            if pan_match:
                data["pan"] = pan_match.group(1)
            else:
                # Fallback: take after colon and clean
                pan_part = line.split(":")[-1].strip()
                # Remove any non-alphanumeric
                pan_clean = re.sub(r'[^A-Za-z0-9]', '', pan_part)
                if len(pan_clean) == 10:
                    data["pan"] = pan_clean.upper()

        elif "scheme" in low:
            data["scheme"] = line.split(":")[-1].strip()

    # =========================
    # TABLE EXTRACTION
    # =========================
    tables = extract_tables(md_text)

    # Print tables in markdown format
    for i, table in enumerate(tables, 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": tables
    }