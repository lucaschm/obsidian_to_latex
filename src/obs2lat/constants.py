import re

INCLUDE_IMAGES = False

FOLDER_REGEX = re.compile(r"^[1-9]$")
CHAPTER_PREFIX_REGEX = re.compile(r"^(\d+(\.\d+)*)")
OBSIDIAN_EMBED_REGEX = re.compile(r"!\[\[(.*?)\]\]")

YAML_HEADER_REGEX = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
NOTES_SECTION_REGEX = re.compile(r"^##\s*Notes.*", re.IGNORECASE | re.DOTALL)
