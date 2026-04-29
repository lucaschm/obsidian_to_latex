import pypandoc

from collections import defaultdict
import os
from pathlib import Path
from typing import List, Dict, Optional

from obs2lat.constants import *


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

        # 1. Exact match (full relative path with extension)
        if name in self.by_relpath:
            return self.by_relpath[name]

        # 2. If extension is present -> match by filename EXACTLY
        if "." in Path(name).name:
            filename = Path(name).name

            matches = [
                path for path in self.by_stem.get(Path(name).stem, [])
                if path.name == filename
            ]

            if len(matches) == 1:
                return matches[0]

            if len(matches) > 1:
                print(f"Warning: multiple exact matches for '{name}', using first: {matches[0]}")
                return matches[0]

            return None  # IMPORTANT: do NOT fallback to wrong file

        # 3. No extension -> fallback to stem match
        stem = Path(name).stem
        matches = self.by_stem.get(stem, [])

        if not matches:
            return None

        if len(matches) > 1:
            print(f"Warning: multiple matches for '{name}', using first: {matches[0]}")

        return matches[0]
