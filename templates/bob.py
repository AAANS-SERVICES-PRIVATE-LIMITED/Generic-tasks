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

    # BOB specific extraction
    # First line contains name: "DHARMENDRA KUMAR Customer ID: XXXXX4288..."
    if lines:
        first_line = lines[0]
        # Name is before "Customer ID" - case insensitive, flexible spacing
        match = re.search(r'^(.+?)\s+customer\s+id\s*[:\-]?\s*', first_line, re.IGNORECASE)
        if match:
            data["name"] = match.group(1).strip()

    for i, line in enumerate(lines):
        low = line.lower()

        # Customer ID - capture until space or non-alphanumeric
        if "customer id" in low:
            match = re.search(r'customer\s*id[:\s]+([A-Za-z0-9X]+)', line, re.IGNORECASE)
            if match:
                data["customer_id"] = match.group(1)

        # Account Number
        elif "account no" in low:
            match = re.search(r'account\s*no[-:\s]+(\d+)', line, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)

        # PAN (if available)
        elif re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', line):
            match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', line)
            if match:
                data["pan"] = match.group(0)

        # Statement period
        elif "detailed statement" in low and "between" in low:
            match = re.search(r'between\s+(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})', line, re.IGNORECASE)
            if match:
                data["statement_from"] = match.group(1)
                data["statement_to"] = match.group(2)

    # === EXTRACT FROM OCR TEXT (for grey box data that MinerU misses) ===
    if ocr_text:
        ocr_lines = [clean(l) for l in ocr_text.split("\n") if l.strip()]
        print(f"\nDEBUG: Extracting from OCR text ({len(ocr_lines)} lines)")
        print("  First 10 OCR lines:")
        for i, l in enumerate(ocr_lines[:10]):
            print(f"    {i}: {l}")

        for line in ocr_lines:
            low = line.lower()

            # Branch from OCR - pattern: Branch-DAHIYAWAN or Branch-DAHIVAWAN
            if "branch-" in low or "branch:" in low:
                match = re.search(r'branch[-:\s]+([A-Za-z]+)', line, re.IGNORECASE)
                if match and not data.get("branch"):
                    data["branch"] = match.group(1)
                    print(f"  Found branch in OCR: {data['branch']}")

            # IFSC Code from OCR - pattern: BARBODAHIVAWAN or BARB + branch
            # BOB IFSC starts with BARB followed by branch name (without vowels sometimes)
            if "barb" in low or "ifsc" in low or "baroda" in low:
                # Look for BARB followed by letters/numbers (full IFSC)
                match = re.search(r'barb[a-z0-9]+', line, re.IGNORECASE)
                if match and not data.get("ifsc"):
                    data["ifsc"] = match.group(0).upper()
                    print(f"  Found IFSC in OCR: {data['ifsc']}")
                # Also try pattern: IFSC Code: BARB...
                match = re.search(r'ifsc\s*code[:\-\s]+([a-z0-9]+)', line, re.IGNORECASE)
                if match and not data.get("ifsc"):
                    data["ifsc"] = match.group(1).upper()
                    print(f"  Found IFSC in OCR: {data['ifsc']}")

            # MICR Code from OCR - pattern: MICR Code-211015214 or just 211015214
            if "micr" in low:
                match = re.search(r'micr\s*code[-:\s]*(\d+)', line, re.IGNORECASE)
                if match and not data.get("micr"):
                    data["micr"] = match.group(1)
                    print(f"  Found MICR in OCR: {data['micr']}")
                else:
                    # Try standalone 9 digit number near MICR
                    match = re.search(r'micr.*?(\d{9})', line, re.IGNORECASE)
                    if match and not data.get("micr"):
                        data["micr"] = match.group(1)
                        print(f"  Found MICR in OCR: {data['micr']}")

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
