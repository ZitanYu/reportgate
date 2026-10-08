"""Read-only access to the maintainer's local checkout.

reportgate never writes to the checkout. Every path from a report is checked
twice before anything is read: lexically (absolute paths and ``..`` that climb
out are rejected) and after resolving symbolic links (a link that points outside
the checkout is rejected). A rejected path is reported as escaping the
repository and is never opened.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .errors import CheckoutError
from .extract import lexically_escapes
from .text import norm_line

SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        "dist",
        "build",
        "target",
        ".mypy_cache",
        ".pytest_cache",
    }
)


def _within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # different drives on Windows
        return False


class Tree:
    """A checkout on disk, or no checkout at all (``root=None``)."""

    MAX_READ_BYTES = 5_000_000
    SEARCH_MAX_FILES = 20_000
    SEARCH_MAX_BYTES = 1_000_000

    def __init__(self, root: "os.PathLike[str] | str | None" = None) -> None:
        self.root: Optional[Path] = None
        self._real_root: Optional[str] = None
        self._texts: Dict[str, Optional[Tuple[int, str]]] = {}
        self._index: Optional[List[Tuple[str, str]]] = None
        if root is not None:
            path = Path(root)
            if not path.is_dir():
                raise CheckoutError("checkout not found or not a directory: %s" % path.as_posix())
            self.root = path
            self._real_root = os.path.realpath(path)

    @property
    def checked(self) -> bool:
        return self.root is not None

    def _resolve(self, rel: str) -> Optional[str]:
        """Real path of ``rel`` if it stays inside the checkout, else ``None``."""
        if self._real_root is None or lexically_escapes(rel):
            return None
        full = os.path.realpath(os.path.join(self._real_root, rel))
        return full if _within(full, self._real_root) else None

    def locate(self, rel: str) -> Tuple[bool, Optional[bool]]:
        """Return ``(escapes_repo, exists)`` for a repository-relative path.

        ``exists`` is ``None`` when there is no checkout or the path escapes.
        """
        if lexically_escapes(rel):
            return True, None
        if self._real_root is None:
            return False, None
        full = self._resolve(rel)
        if full is None:
            return True, None
        return False, os.path.isfile(full)

    def text(self, rel: str) -> Optional[Tuple[int, str]]:
        """``(line_count, whitespace-normalised text)`` of a file in the checkout."""
        if rel in self._texts:
            return self._texts[rel]
        value: Optional[Tuple[int, str]] = None
        full = self._resolve(rel)
        if full is not None and os.path.isfile(full):
            try:
                if os.path.getsize(full) <= self.MAX_READ_BYTES:
                    with open(full, "r", encoding="utf-8", errors="replace") as handle:
                        lines = handle.read().splitlines()
                    value = (len(lines), "\n".join(norm_line(line) for line in lines))
            except OSError:
                value = None
        self._texts[rel] = value
        return value

    def search_index(self) -> List[Tuple[str, str]]:
        """Normalised text of text files in the checkout, for finding moved code.

        Skips VCS and build directories, hidden directories, binary files, files
        over :attr:`SEARCH_MAX_BYTES`, and links that leave the checkout. Built once.
        """
        if self._index is not None:
            return self._index
        index: List[Tuple[str, str]] = []
        if self._real_root is None:
            self._index = index
            return index
        count = 0
        for dirpath, dirnames, filenames in os.walk(self._real_root, followlinks=False):
            dirnames[:] = sorted(
                d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
            )
            for name in sorted(filenames):
                if count >= self.SEARCH_MAX_FILES:
                    self._index = index
                    return index
                full = os.path.join(dirpath, name)
                real = os.path.realpath(full)
                if not _within(real, self._real_root) or not os.path.isfile(real):
                    continue
                try:
                    if os.path.getsize(real) > self.SEARCH_MAX_BYTES:
                        continue
                    with open(real, "rb") as handle:
                        data = handle.read()
                except OSError:
                    continue
                if b"\0" in data[:4096]:
                    continue
                count += 1
                rel = Path(os.path.relpath(full, self._real_root)).as_posix()
                text = data.decode("utf-8", errors="replace")
                index.append((rel, "\n".join(norm_line(line) for line in text.splitlines())))
        self._index = index
        return index
