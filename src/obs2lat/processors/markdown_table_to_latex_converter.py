import re

from .content_processor import ContentProcessor 

class MarkdownTableToLatexProcessor(ContentProcessor):
    def process(self, text: str) -> str:
        return re.sub(
            r"(\|.+\|\n\|[-\s|]+\|\n(?:\|.*\|\n?)*)",
            self.convert_table,
            text
        )

    def convert_table(self, match):
        table_md = match.group(1).strip()
        lines = table_md.split("\n")

        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        rows = [
            [c.strip() for c in line.strip("|").split("|")]
            for line in lines[2:]
        ]

        col_count = len(headers)

        # First columns fixed, last column flexible
        col_spec = " ".join(["l"] * (col_count - 1) + ["X"])

        latex = []
        latex.append(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}")
        
        # Header
        header_line = " & ".join(f"\\textbf{{{h}}}" for h in headers)
        latex.append(header_line + " \\\\")
        latex.append("\\hline")

        # Rows
        for row in rows:
            latex.append(" & ".join(row) + " \\\\")

        latex.append("\\end{tabularx}")

        return "\n".join(latex)