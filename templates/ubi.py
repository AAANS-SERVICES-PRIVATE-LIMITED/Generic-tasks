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

    # UBI specific extraction - simple line-by-line format
    # First few lines are name and address
    address_lines = []
    in_address = False

    for i, line in enumerate(lines):
        low = line.lower()

        # Name is usually one of the first lines (before "Union Bank")
        if "union bank of india" in low:
            # Name should be in previous lines
            if i >= 1 and not data.get("name"):
                # Check if previous line looks like a name (only letters/spaces)
                prev_line = lines[i-1]
                if prev_line.replace(' ', '').isalpha() and len(prev_line) > 2:
                    data["name"] = prev_line
            continue

        # Branch line
        elif "branch" in low and "jamnagar" in low:
            match = re.search(r'branch\s+(.+)', line, re.IGNORECASE)
            if match:
                data["branch"] = match.group(1).strip()

        # Customer Id (handle OCR error: "ld" instead of "id")
        elif "customer" in low and ("id" in low or "ld" in low):
            match = re.search(r'customer\s*[il]d\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["customer_id"] = match.group(1)
            else:
                # Try next line
                if i + 1 < len(lines) and lines[i+1].strip().isdigit():
                    data["customer_id"] = lines[i+1].strip()

        # Account No
        elif "account no" in low:
            match = re.search(r'account\s*no\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)
            else:
                # Try next line
                if i + 1 < len(lines) and lines[i+1].strip().isdigit():
                    data["account_number"] = lines[i+1].strip()

        # Mobile No
        elif "mobile no" in low:
            # Mobile is on next line or in current line
            match = re.search(r'mobile\s*no\s*(\d+)', line, re.IGNORECASE)
            if match:
                data["mobile"] = match.group(1)
            elif i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line.isdigit():
                    data["mobile"] = next_line

        # Account Currency
        elif "account currency" in low:
            match = re.search(r'account\s*currency\s*(\w+)', line, re.IGNORECASE)
            if match:
                data["currency"] = match.group(1)
            else:
                # Try next line
                if i + 1 < len(lines):
                    data["currency"] = lines[i+1].strip()

        # Account Type
        elif "account type" in low:
            match = re.search(r'account\s*type\s*(.+)', line, re.IGNORECASE)
            if match:
                data["account_type"] = match.group(1).strip()
            else:
                if i + 1 < len(lines):
                    data["account_type"] = lines[i+1].strip()

        # Email
        elif "e-mail" in low or "email" in low:
            match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', line)
            if match:
                data["email"] = match.group(0)
            else:
                # Try next line
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if '@' in next_line:
                        data["email"] = next_line

        # Statement Date
        elif "statement date" in low:
            match = re.search(r'statement\s*date[:\s]+(.+)', line, re.IGNORECASE)
            if match:
                data["statement_date"] = match.group(1).strip()
            else:
                # Try next line
                if i + 1 < len(lines):
                    data["statement_date"] = lines[i+1].strip()

        # Statement Period
        elif "statement period" in low:
            match = re.search(r'statement\s*period\s*from[-\s]*([\d/]+)\s*to\s*([\d/]+)', line, re.IGNORECASE)
            if match:
                data["statement_from"] = match.group(1)
                data["statement_to"] = match.group(2)
            else:
                # Try next line for period info
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    match = re.search(r'from[-\s]*([\d/]+)\s*to\s*([\d/]+)', next_line, re.IGNORECASE)
                    if match:
                        data["statement_from"] = match.group(1)
                        data["statement_to"] = match.group(2)

        # Address lines (before bank name and after name)
        elif not data.get("name") and line.replace(' ', '').isalpha() and len(line) > 3:
            # This could be the name if it's before bank name
            pass

        # ZIP code
        elif line.strip().isdigit() and len(line.strip()) == 6:
            data["zip"] = line.strip()

        # City and State detection
        elif "city" in low:
            if i + 1 < len(lines):
                city_val = lines[i+1].strip()
                if city_val and city_val.lower() not in ['stae', 'state', 'country', 'zip']:
                    data["city"] = city_val

        elif "state" in low or "stae" in low:
            if i + 1 < len(lines):
                state_val = lines[i+1].strip()
                if state_val and state_val.lower() not in ['country', 'zip']:
                    data["state"] = state_val

        elif "country" in low:
            if i + 1 < len(lines):
                country_val = lines[i+1].strip()
                if country_val:
                    data["country"] = country_val

    # Try to find name from first few lines if not found
    if not data.get("name"):
        for line in lines[:5]:
            if line.replace(' ', '').isalpha() and len(line) > 3 and line.lower() not in ['statement of account']:
                data["name"] = line
                break

    # Build address from components if available
    addr_parts = []
    for key in ['address_line1', 'address_line2', 'city', 'state', 'country', 'zip']:
        if data.get(key):
            addr_parts.append(data[key])

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
