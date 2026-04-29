import re

from .content_processor import ContentProcessor 
from obs2lat.constants import *

class YAMLRemover(ContentProcessor):
    def process(self, text: str) -> str:
        return re.sub(YAML_HEADER_REGEX, "", text)