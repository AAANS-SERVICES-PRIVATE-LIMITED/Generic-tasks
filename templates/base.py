"""
base.py — Shared utilities for all bank templates.

Import from here instead of copy-pasting into each template:
    from .base import clean, extract_tables, table_to_markdown
"""

import re
import logging
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


def clean(text: str) -> str:
    """Strip leading/trailing whitespace from a string."""
    return text.strip()


class TableParser(HTMLParser):
    """HTML parser that extracts <table> data into nested Python lists."""

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
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif tag == "tr":
            self.in_row = True
            self.current_row = []
        elif tag in ("td", "th"):
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
            if self.current_table:
                self.tables.append(self.current_table)
        elif tag == "tr":
            self.in_row = False
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag in ("td", "th"):
            self.in_cell = False
            cell_text = "".join(self.current_cell).strip()
            self.current_row.append(cell_text)

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)


def extract_tables(md_text: str) -> list:
    """
    Extract all HTML <table>...</table> blocks from MinerU markdown output.

    Returns a list of tables; each table is a list of rows; each row is a list
    of cell strings.
    """
    if not md_text:
        return []

    table_pattern = r"<table>.*?</table>"
    table_matches = re.findall(table_pattern, md_text, re.DOTALL | re.IGNORECASE)

    all_tables = []
    for table_html in table_matches:
        try:
            parser = TableParser()
            parser.feed(table_html)
            if parser.tables:
                all_tables.extend(parser.tables)
        except Exception as exc:
            logger.warning("Failed to parse a table block: %s", exc)

    return all_tables


def table_to_markdown(table: list) -> str:
    """Convert a parsed table (list of rows) to a GitHub-flavoured markdown table string."""
    if not table:
        return ""

    md_lines = []
    header = table[0]
    md_lines.append("| " + " | ".join(str(cell) for cell in header) + " |")
    md_lines.append("|" + "|".join(" --- " for _ in header) + "|")
    for row in table[1:]:
        md_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return "\n".join(md_lines)
