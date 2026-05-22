import re

from .content_processor import ContentProcessor 
from obs2lat.constants import *
from obs2lat.util import latex_escape

class ObsidianLinkConverter(ContentProcessor):
    def __init__(self, mode="bold"):
        self.mode = mode  # "bold", "gls", or custom later

    def process(self, text: str) -> str:
        return re.sub(r"\[\[([^\]]+)\]\]", self.replace_link, text)

    def replace_link(self, match):
        content = match.group(1)

        # Split alias if present
        if "|" in content:
            target, alias = content.split("|", 1)
        else:
            target, alias = content, content

        label = alias.strip()
        key = target.strip()

        return self.format_output(label, key)

    def format_output(self, label: str, key: str) -> str:
        label = latex_escape(label)
        key = latex_escape(key)
        
        if self.mode == "bold":
            return f"\\textbf{{{label}}}"
        
        elif self.mode == "italic":
            return f"\\textit{{{label}}}"

        elif self.mode == "gls":
            return f"\\gls{{{key}}}"

        # fallback (easy to extend)
        return label
