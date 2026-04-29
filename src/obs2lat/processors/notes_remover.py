import re

from .content_processor import ContentProcessor 
from obs2lat.constants import *

class NotesRemover(ContentProcessor):
    def process(self, text: str) -> str:
        match = re.search(r"^##\s*Notes", text, re.IGNORECASE | re.MULTILINE)
        if match:
            return text[:match.start()]
        return text
