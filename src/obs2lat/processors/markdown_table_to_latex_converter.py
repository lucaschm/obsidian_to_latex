import re

from .content_processor import ContentProcessor
from obs2lat.util import latex_escape


class MarkdownTableToLatexProcessor(ContentProcessor):

    TABLE_PATTERN = re.compile(
        r"""
        (?P<table>
            \|.+\|\n
            \|[-\s|]+\|\n
            (?:\|.*\|\n?)*
        )
        (?P<annotations>
            (?:
                \n\s*
                %%.*?%%
            )*
        )
        """,
        re.VERBOSE | re.MULTILINE,
    )

    ANNOTATION_PATTERN = re.compile(
        r"""
        %%
        \s*
        (?P<key>[a-zA-Z]+)
        \s*:\s*
        (?P<value>.*?)
        \s*
        %%
        """,
        re.VERBOSE,
    )

    def process(self, text: str) -> str:
        return self.TABLE_PATTERN.sub(self.convert_table, text)

    def convert_table(self, match: re.Match) -> str:
        table_md = match.group("table").strip()
        annotations = match.group("annotations") or ""

        metadata = self.parse_annotations(annotations)

        caption = metadata.get("caption")
        label = metadata.get("label")

        lines = table_md.split("\n")

        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        rows = [
            [c.strip() for c in line.strip("|").split("|")]
            for line in lines[2:]
        ]

        headers = [latex_escape(h) for h in headers]
        rows = [
            [latex_escape(c) for c in row]
            for row in rows
        ]

        col_count = len(headers)
        col_spec = " ".join(["l"] * (col_count - 1) + ["X"])

        latex = []

        if caption or label:
            latex.append(r"\begin{table}[H]")
            latex.append(r"\centering")

        latex.append(
            rf"\begin{{tabularx}}{{\textwidth}}{{{col_spec}}}"
        )

        header_line = " & ".join(
            f"\\textbf{{{h}}}" for h in headers
        )

        latex.append(header_line + r" \\")
        latex.append(r"\hline")

        for row in rows:
            latex.append(" & ".join(row) + r" \\")

        latex.append(r"\end{tabularx}")

        if caption:
            latex.append(
                rf"\caption{{{latex_escape(caption)}}}"
            )

        if label:
            latex.append(
                rf"\label{{{latex_escape(label)}}}"
            )

        if caption or label:
            latex.append(r"\end{table}")

        return "\n".join(latex)

    def parse_annotations(self, text: str) -> dict[str, str]:
        metadata = {}

        for match in self.ANNOTATION_PATTERN.finditer(text):
            key = match.group("key").strip().lower()
            value = match.group("value").strip()

            metadata[key] = value

        return metadata