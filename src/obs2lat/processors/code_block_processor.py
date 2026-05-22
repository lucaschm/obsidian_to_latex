import re

from .content_processor import ContentProcessor
from obs2lat.util import latex_escape

class CodeBlockProcessor(ContentProcessor):
    DEFAULT_SEPARATOR = ","

    def __init__(self, separator: str = DEFAULT_SEPARATOR):
        self.separator = separator

    def process(self, text: str) -> str:
        pattern = re.compile(
            r"```([^\n]*)\n(.*?)```",
            re.DOTALL
        )

        return pattern.sub(self.replace_block, text)

    def replace_block(self, match: re.Match) -> str:
        metadata = match.group(1).strip()
        code = match.group(2)

        style, caption, label = self.parse_metadata(metadata)

        options = []

        if style:
            options.append(f"style={style}")

        if caption:
            escaped_caption = latex_escape(caption)
            options.append(f"caption={{{escaped_caption}}}")

        if label:
            options.append(f"label={{{label}}}")

        option_string = ""
        if options:
            option_string = "[" + ", ".join(options) + "]"

        return (
            f"\\begin{{lstlisting}}{option_string}\n"
            f"{code.rstrip()}\n"
            f"\\end{{lstlisting}}"
        )

    def parse_metadata(
        self,
        metadata: str
    ) -> tuple[str | None, str | None, str | None]:
        """
        Metadata format:

        ```style, caption, label

        Examples:
        ```python
        ```python, My Caption
        ```python, My Caption, my_label
        """

        if not metadata:
            return None, None, None

        parts = [p.strip() for p in metadata.split(self.separator)]

        style = parts[0] if len(parts) >= 1 else None
        caption = parts[1] if len(parts) >= 2 else None
        label = parts[2] if len(parts) >= 3 else None

        return (
            style or None,
            caption or None,
            label or None
        )
