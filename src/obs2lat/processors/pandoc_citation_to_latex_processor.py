import re

from .content_processor import ContentProcessor 
from obs2lat.constants import *

class PandocCitationToLatexProcessor(ContentProcessor):
    def process(self, text: str) -> str:
        # [@key] → \cite{key}
        text = re.sub(r"\[@([a-zA-Z0-9:_-]+)\]", r"\\cite{\1}", text)

        # [@key1; @key2] → \cite{key1,key2}
        def multi_cite(match):
            keys = re.findall(r"@([a-zA-Z0-9:_-]+)", match.group(0))
            return "\\cite{" + ",".join(keys) + "}"

        text = re.sub(r"\[(?:@[^\]]+;?\s*)+\]", multi_cite, text)

        return text
