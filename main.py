import pypandoc

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

# =========================
# Configuration (Adjustable)
# =========================

INCLUDE_IMAGES = False

FOLDER_REGEX = re.compile(r"^[1-9]$")
CHAPTER_PREFIX_REGEX = re.compile(r"^(\d+(\.\d+)*)")
OBSIDIAN_EMBED_REGEX = re.compile(r"!\[\[(.*?)\]\]")

YAML_HEADER_REGEX = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
NOTES_SECTION_REGEX = re.compile(r"^##\s*Notes.*", re.IGNORECASE | re.DOTALL)


# =========================
# Utility Functions
# =========================

def extract_chapter_prefix(filename: str) -> Optional[str]:
    match = CHAPTER_PREFIX_REGEX.match(filename)
    return match.group(1) if match else None


def sort_key(prefix: str):
    return [int(x) for x in prefix.split(".")]


# =========================
# File Index (for macro lookup)
# =========================

from collections import defaultdict

class FileIndex:
    def __init__(self, root: Path):
        self.root = root
        self.by_stem: Dict[str, List[Path]] = defaultdict(list)
        self.by_relpath: Dict[str, Path] = {}

        self.build_index(root)

    def build_index(self, root: Path):
        import os

        visited = set()

        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirpath = Path(dirpath)

            real_dir = dirpath.resolve()
            if real_dir in visited:
                continue
            visited.add(real_dir)

            for filename in filenames:
                path = dirpath / filename  # ← IMPORTANT: keep logical path

                try:
                    resolved = path.resolve()
                except Exception:
                    continue

                # THIS is what Obsidian uses
                rel = path.relative_to(root).as_posix()

                # Store lookup keys (Obsidian-style)
                self.by_relpath[rel] = resolved
                self.by_relpath[str(Path(rel).with_suffix(""))] = resolved

                # Stem lookup
                self.by_stem[path.stem].append(resolved)

    def find(self, name: str) -> Optional[Path]:
        name = name.strip()

        # Normalize path format
        name = name.replace("\\", "/")

        # 1. Direct relative path match
        if name in self.by_relpath:
            return self.by_relpath[name]

        # 2. Try adding extension (if missing)
        if "." not in Path(name).name:
            for ext in [".md", ".png", ".jpg", ".jpeg", ".pdf"]:
                candidate = name + ext
                if candidate in self.by_relpath:
                    return self.by_relpath[candidate]

        # 3. Fallback: filename only
        stem = Path(name).stem
        matches = self.by_stem.get(stem, [])

        if not matches:
            return None

        if len(matches) > 1:
            print(f"Warning: multiple matches for '{name}', using first: {matches[0]}")

        return matches[0]
# =========================
# Content Processors
# =========================

class ContentProcessor:
    def process(self, text: str) -> str:
        return text


class YAMLRemover(ContentProcessor):
    def process(self, text: str) -> str:
        return re.sub(YAML_HEADER_REGEX, "", text)


class NotesRemover(ContentProcessor):
    def process(self, text: str) -> str:
        match = re.search(r"^##\s*Notes", text, re.IGNORECASE | re.MULTILINE)
        if match:
            return text[:match.start()]
        return text


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
        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".pdf"]:
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
        if self.mode == "bold":
            return f"\\textbf{{{label}}}"

        elif self.mode == "gls":
            return f"\\gls{{{key}}}"

        # fallback (easy to extend)
        return label

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


class PandocConverter(ContentProcessor):
    def process(self, text: str) -> str:
        return pypandoc.convert_text(text, "latex", format="md")

# =========================
# Core Processing Pipeline
# =========================

class ProcessingPipeline:
    def __init__(self, processors: List[ContentProcessor]):
        self.processors = processors

    def run(self, text: str) -> str:
        for processor in self.processors:
            text = processor.process(text)
        return text


# =========================
# Main Generator
# =========================

class LatexGenerator:
    def __init__(self, root: Path, output_dir: Path):
        self.root = root
        self.file_index = FileIndex(root)
        self.output_dir = output_dir

        self.pipeline = ProcessingPipeline([
            YAMLRemover(),
            NotesRemover(),
            ObsidianMacroResolver(self.file_index),
            ObsidianLinkConverter(mode="bold"),
            PandocCitationToLatexProcessor(),
            PandocConverter()
        ])

    def generate(self):
        for folder in self.root.iterdir():
            if folder.is_dir() and FOLDER_REGEX.match(folder.name):
                self.process_folder(folder)

    def process_folder(self, folder: Path):
        files = []

        for file in folder.iterdir():
            if file.is_file():
                prefix = extract_chapter_prefix(file.name)
                if prefix:
                    files.append((prefix, file))

        files.sort(key=lambda x: sort_key(x[0]))

        output = []

        for prefix, file in files:
            section_title = file.stem[len(prefix):].strip(" ._-")
            content = file.read_text(encoding="utf-8")

            processed = self.pipeline.run(content)

            output.append(f"\\section{{{section_title}}}")
            output.append(processed)

        output_path = self.output_dir / f"{folder.name}.tex"
        output_path.write_text("\n\n".join(output), encoding="utf-8")


# =========================
# Entry Point
# =========================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert Obsidian notes to LaTeX")
    parser.add_argument("root", type=str, help="Root directory path")
    parser.add_argument("output", type=str, help="Output directory path")

    args = parser.parse_args()

    root = Path(args.root)
    output_dir = Path(args.output)
    generator = LatexGenerator(root, output_dir)
    generator.generate()


if __name__ == "__main__":
    main()