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

    # CBI specific extraction
    for i, line in enumerate(lines):
        low = line.lower()

        # Account number from statement header: "Statement for A/c 3762413136"
        if "statement for a/c" in low:
            match = re.search(r'statement\s+for\s+a/c\s+(\d+)', line, re.IGNORECASE)
            if match:
                data["account_number"] = match.group(1)

        # Statement period: "between 22-Apr-2023 and 22-Jul-2023"
        elif "between" in low:
            match = re.search(r'between\s+(\d{2}-[A-Za-z]{3}-\d{4})\s+and\s+(\d{2}-[A-Za-z]{3}-\d{4})', line, re.IGNORECASE)
            if match:
                data["statement_from"] = match.group(1)
                data["statement_to"] = match.group(2)

    # Parse tables for metadata (CBI has metadata in first 2 tables)
    tables = extract_tables(md_text)

    # === FIRST TABLE: Client Info ===
    # Parse raw HTML to get proper field names (MinerU merges "Client Code Name" into one)
    client_table_html = re.search(r'<table>.*?</table>', md_text, re.DOTALL | re.IGNORECASE)
    if client_table_html:
        html = client_table_html.group(0)
        # Extract all td content pairs
        rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL | re.IGNORECASE)

        for i, row in enumerate(rows):
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if len(cells) >= 2:
                key = clean(cells[0]).lower()
                value = clean(cells[1])

                # MinerU merges "Client Code Name" into one field
                # The actual name appears in the Address row as first part
                if "client code name" in key:
                    data["client_code"] = value
                elif "address" in key:
                    # For CBI, name appears merged with address due to MinerU parsing
                    # Format: "SABAFAROOQ NADAF PLOTNO70KHATIB NAGAR..."
                    # Look for address keywords or numbers to split name from address
                    address_keywords = ['plot', 'khati', 'khatib', 'nagar', 'road', 'lane', 'street', 'flat', 'building', 'tower']
                    parts = value.split()

                    name_parts = []
                    addr_parts = []
                    found_addr = False

                    for part in parts:
                        low_part = part.lower()
                        # Check if this part looks like address (contains number or address keyword)
                        has_number = any(c.isdigit() for c in part)
                        is_addr_keyword = any(kw in low_part for kw in address_keywords)

                        if not found_addr and (has_number or is_addr_keyword):
                            found_addr = True

                        if not found_addr:
                            name_parts.append(part)
                        else:
                            addr_parts.append(part)

                    if name_parts:
                        data["name"] = " ".join(name_parts)
                    if addr_parts:
                        data["customer_address"] = " ".join(addr_parts)
                elif "phone" in key:
                    data["phone"] = value

    # === SECOND TABLE: Branch Info ===
    # Find second table
    all_tables_html = re.findall(r'<table>.*?</table>', md_text, re.DOTALL | re.IGNORECASE)
    if len(all_tables_html) > 1:
        branch_html = all_tables_html[1]
        rows = re.findall(r'<tr[^>]*>.*?</tr>', branch_html, re.DOTALL | re.IGNORECASE)

        in_branch_address = False
        branch_addr_lines = []

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if not cells:
                continue

            # Check for rowspan in first cell (indicates continuation)
            has_rowspan = 'rowspan' in row.lower()

            if len(cells) >= 2:
                key = clean(cells[0]).lower()
                value = clean(cells[1])

                if "branch code" in key:
                    # Extract just the number
                    match = re.search(r'(\d+)', value)
                    if match:
                        data["branch_code"] = match.group(1)
                    in_branch_address = False
                elif "branch name" in key:
                    data["branch_name"] = value
                    in_branch_address = False
                elif "address" in key:
                    in_branch_address = True
                    branch_addr_lines = [value]
                elif "ifsc" in key:
                    # Extract CBIN code
                    match = re.search(r'CBIN\d+', value, re.IGNORECASE)
                    if match:
                        data["ifsc"] = match.group(0).upper()
                    in_branch_address = False
            elif len(cells) == 1 and has_rowspan and in_branch_address:
                # Continuation of address (rowspan cell)
                branch_addr_lines.append(clean(cells[0]))

        if branch_addr_lines:
            data["branch_address"] = " ".join(branch_addr_lines)

    # Also try to get from parsed tables as fallback
    if tables:
        # First table - client info
        if len(tables) > 0 and not data.get("client_code"):
            for row in tables[0]:
                if len(row) >= 2:
                    key = row[0].lower()
                    value = row[1]
                    if "client code" in key:
                        data["client_code"] = value
                    elif "phone" in key:
                        data["phone"] = value

        # Second table - branch info
        if len(tables) > 1:
            for row in tables[1]:
                if len(row) >= 2:
                    key = row[0].lower()
                    value = row[1]
                    if "branch code" in key and not data.get("branch_code"):
                        match = re.search(r'(\d+)', value)
                        if match:
                            data["branch_code"] = match.group(1)
                    elif "branch name" in key and not data.get("branch_name"):
                        data["branch_name"] = value
                    elif "ifsc" in key and not data.get("ifsc"):
                        match = re.search(r'CBIN\d+', value, re.IGNORECASE)
                        if match:
                            data["ifsc"] = match.group(0).upper()

    # Clean up: remove tables that are metadata tables (keep only transaction table)
    # Transaction table has Date, Particulars, Withdrawals, Deposits, Balance columns
    transaction_tables = []
    for table in tables:
        if table and len(table[0]) >= 4:  # Check header row
            header = [h.lower() for h in table[0]]
            if any("date" in h for h in header) and any("particulars" in h or "description" in h for h in header):
                transaction_tables.append(table)

    # Print tables in markdown format
    for i, table in enumerate(transaction_tables, 1):
        print(f"\n### Table {i}")
        print(table_to_markdown(table))

    return {
        "metadata": data,
        "tables": transaction_tables
    }
