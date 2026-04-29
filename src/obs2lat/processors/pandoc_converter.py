import pypandoc

from .content_processor import ContentProcessor 
from obs2lat.constants import *

class PandocConverter(ContentProcessor):
    def process(self, text: str) -> str:
        return pypandoc.convert_text(text, "latex", format="md")
