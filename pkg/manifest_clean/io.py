"""File, directory, and stdin I/O for manifest inputs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

from ruamel.yaml import YAML


def _load_yaml_stream(stream, filename: str = "<stdin>"):
    """Load multi-document YAML from a stream. Yields (doc_index, doc_dict)."""
    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        for idx, doc in enumerate(yaml.load_all(stream)):
            if doc is None:
                continue
            if not isinstance(doc, dict):
                raise ValueError(
                    f"{filename}: document {idx}: expected mapping, got {type(doc).__name__}"
                )
            yield idx, doc
    except Exception as e:
        raise type(e)(f"{filename}: {e}") from e


def iter_paths(path_arg: str | None) -> Iterator[Path]:
    """Yield single path for file, or all *.yaml, *.yml, *.json under directory."""
    if path_arg is None or path_arg == "-":
        return
    p = Path(path_arg)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.is_file():
        yield p
        return
    for ext in ("*.yaml", "*.yml", "*.json"):
        yield from sorted(p.rglob(ext))


def load_documents_from_path(
    path: Path,
) -> Iterator[tuple[int, dict]]:
    """Yield (doc_index, doc) for each document in path (file). path must be a file."""
    suffix = path.suffix.lower()
    if suffix not in (".yaml", ".yml", ".json"):
        return
    with open(path, "r", encoding="utf-8") as f:
        for item in _load_yaml_stream(f, str(path)):
            yield item


def load_documents_from_stdin() -> Iterator[tuple[int, dict]]:
    """Yield (doc_index, doc) for each document from stdin."""
    for item in _load_yaml_stream(sys.stdin, "<stdin>"):
        yield item
