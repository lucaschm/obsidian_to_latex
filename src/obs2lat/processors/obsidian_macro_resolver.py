import re

from .content_processor import ContentProcessor 
from obs2lat.file_index import FileIndex
from obs2lat.constants import *

class ObsidianMacroResolver(ContentProcessor):
    def __init__(self, file_index: FileIndex):
        self.file_index = file_index

    def process(self, text: str, stack=None) -> str:
        if stack is None:
            stack = []

        return re.sub(
            OBSIDIAN_EMBED_REGEX,
            lambda m: self.replace_embed(m, stack),
            text
        )

    def replace_embed(self, match, stack):
        target = match.group(1)

        if "#" in target:
            filename, heading = target.split("#", 1)
        else:
            filename, heading = target, None

        path = self.file_index.find(filename)
        if not path:
            return ""

        # --- CYCLE DETECTION ---
        if path in stack:
            cycle = " -> ".join(p.name for p in stack + [path])
            raise RuntimeError(f"Cycle detected: {cycle}")

        # --- IMAGE HANDLING ---
        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg"]:
            if INCLUDE_IMAGES:
                return f"\\includegraphics[width=\\textwidth]{{{path.as_posix()}}}"
            else:
                return ""
        # --- RECURSION ---
        new_stack = stack + [path]

        content = path.read_text(encoding="utf-8")

        # Recursively resolve with updated stack
        content = self.process(content, new_stack)

        if heading:
            content = self.extract_section(content, heading)

        return content

    def extract_section(self, text: str, heading: str) -> str:
        # Match the exact heading and capture its level
        pattern = re.compile(rf"^(#+)\s*{re.escape(heading)}\s*$", re.MULTILINE)
        match = pattern.search(text)

        if not match:
            return ""

        heading_level = len(match.group(1))
        start = match.end()

        # Find next heading with level <= current level
        next_heading_pattern = re.compile(r"^(#+)\s", re.MULTILINE)

        end = len(text)
        for m in next_heading_pattern.finditer(text, start):
            level = len(m.group(1))
            if level <= heading_level:
                end = m.start()
                break

        return text[start:end].strip()
