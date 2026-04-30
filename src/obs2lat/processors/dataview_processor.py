import re
from pathlib import Path
from typing import List, Dict, Tuple

from .content_processor import ContentProcessor 
from obs2lat.constants import *


class SimpleDataviewProcessor(ContentProcessor):
    def __init__(self, root: Path):
        self.root = root

    def process(self, text: str) -> str:
        return re.sub(
            r"```dataview(.*?)```",
            self.replace_dataview,
            text,
            flags=re.DOTALL
        )

    # =========================
    # Core Replacement
    # =========================

    def replace_dataview(self, match):
        query = match.group(1).strip()

        fields, folder = self.parse_query(query)
        if not fields or not folder:
            return "% Unsupported dataview query"

        rows = self.collect_rows(folder, fields)

        return self.build_markdown_table(fields, rows)

    # =========================
    # Query Parsing
    # =========================

    def parse_query(self, query: str) -> Tuple[List[Tuple[str, str]], str]:
        table_match = re.search(r"TABLE\s+(.*?)\n", query, re.IGNORECASE)
        from_match = re.search(r'FROM\s+"([^"]+)"', query, re.IGNORECASE)

        if not table_match or not from_match:
            return [], ""

        field_part = table_match.group(1)
        folder = from_match.group(1)

        fields = []
        for part in field_part.split(","):
            part = part.strip()

            alias_match = re.match(r"(\w+(?:\.\w+)*)\s+as\s+(.+)", part, re.IGNORECASE)
            if alias_match:
                field, alias = alias_match.groups()
            else:
                field, alias = part, part

            fields.append((field.strip(), alias.strip()))

        if not any(f[0].lower() == "file.name" for f in fields):
            fields.insert(0, ("file.name", "File"))

        return fields, folder

    # =========================
    # Data Collection
    # =========================

    def resolve_field(self, field: str, file: Path, metadata: Dict[str, str]):
        field = field.strip()

        # --- Special Dataview fields ---
        if field == "file.name":
            return f"[[{file.stem}]]"
        if field == "file.path":
            return file.as_posix()

        if field == "file.folder":
            return file.parent.name

        # --- YAML metadata fallback ---
        return metadata.get(field, "")

    def collect_rows(self, folder: str, fields: List[Tuple[str, str]]):
        folder_path = self.root / folder
        rows = []

        if not folder_path.exists():
            return rows

        for file in folder_path.glob("*.md"):
            metadata = self.extract_yaml(file)

            row = []
            for field, _ in fields:
                value = self.resolve_field(field, file, metadata)
                row.append(str(value))

            rows.append(row)

        return rows

    # =========================
    # YAML Extraction
    # =========================

    def extract_yaml(self, file: Path) -> Dict[str, str]:
        text = file.read_text(encoding="utf-8")

        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not match:
            return {}

        yaml_text = match.group(1)

        data = {}
        for line in yaml_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        return data

    # =========================
    # Table Builder
    # =========================

    def build_markdown_table(self, fields, rows):
        headers = [alias for _, alias in fields]

        header_line = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"

        body = []
        for row in rows:
            body.append("| " + " | ".join(row) + " |")

        return "\n".join([header_line, separator] + body)