from pathlib import Path
from typing import List, Optional

from obs2lat.processors import *
from obs2lat.file_index import FileIndex
from obs2lat.constants import *


# =========================
# Utility Functions
# =========================

def extract_chapter_prefix(filename: str) -> Optional[str]:
    match = CHAPTER_PREFIX_REGEX.match(filename)
    return match.group(1) if match else None


def sort_key(prefix: str):
    return [int(x) for x in prefix.split(".")]


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
            SimpleDataviewProcessor(self.root, include_file_column=False),
            ObsidianMacroResolver(self.file_index),
            ObsidianLinkConverter(mode="italic"),
            MarkdownTableToLatexProcessor(),
            PandocCitationToLatexProcessor(),
            CodeBlockProcessor(),
            ObsidianCommentRemover(),
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

            if prefix == "0":
                output.append(processed)
            else:
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