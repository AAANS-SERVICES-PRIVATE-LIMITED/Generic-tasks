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

    # SBI specific extraction - colon separated fields
    for line in lines:
        low = line.lower()

        if "account number" in low and ":" in line:
            data["account_number"] = line.split(":")[-1].strip()

        elif "name" in low and ":" in line and "branch" not in low:
            data["name"] = line.split(":")[-1].strip()

        elif "ifs code" in low or "ifsc code" in low:
            data["ifsc"] = line.split(":")[-1].strip()

        elif re.search(r'branch\s*:\s*', line, re.IGNORECASE) and "branchcode" not in low:
            data["branch"] = line.split(":")[-1].strip()

        elif "currency" in low:
            data["currency"] = line.split(":")[-1].strip()

        elif "rate of interest" in low:
            # Match "Rate of Interest (% p.a.) :9.95%"
            match = re.search(r'(\d+\.?\d*)\s*%', line)
            if match:
                data["rate_of_interest"] = match.group(1) + "%"
            else:
                data["rate_of_interest"] = line.split(":")[-1].strip()

        elif "book balance" in low:
            val = line.split(":")[-1].strip()
            data["book_balance"] = val

        elif "available balance" in low and "book" not in low:
            val = line.split(":")[-1].strip()
            data["available_balance"] = val

        elif "hold value" in low:
            data["hold_value"] = line.split(":")[-1].strip()

        elif "uncleared amount" in low:
            data["uncleared_amount"] = line.split(":")[-1].strip()

        elif "drawing power" in low:
            data["drawing_power"] = line.split(":")[-1].strip()

        elif "limit sanctioned" in low:
            data["limit_sanctioned"] = line.split(":")[-1].strip()

        elif re.search(r'balance\s*as\s*on', line, re.IGNORECASE):
            # Match "Balance as on 1 Jan 2018 :-2,44,210.58"
            match = re.search(r'balance\s*as\s*on\s+(.+?)\s*:\s*([-\d,\.]+)', line, re.IGNORECASE)
            if match:
                data["balance_as_on_date"] = match.group(1).strip()
                data["balance_as_on_value"] = match.group(2).strip()

        elif re.search(r'corporate\s*address\s*:\s*', line, re.IGNORECASE):
            addr_parts = [line.split(":")[-1].strip()]
            # Capture continuation lines (next 3 lines that don't start with known fields)
            idx = lines.index(line)
            for j in range(idx + 1, min(idx + 4, len(lines))):
                next_line = lines[j]
                next_low = next_line.lower()
                # Stop if we hit a new field (contains : and a known keyword)
                if ":" in next_line and any(kw in next_low for kw in ["branch", "ifsc", "ifs", "currency", "book balance", "available balance", "rate of interest", "hold value", "uncleared amount", "drawing power", "limit sanctioned"]):
                    break
                # Also stop if we hit a line starting with ' (continuation of address indicator)
                # but contains branch name pattern
                addr_parts.append(next_line.strip())
            data["address"] = " ".join(addr_parts).strip()

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
