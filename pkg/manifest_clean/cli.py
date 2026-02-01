"""CLI logic for kubectl-manifest-clean (library in pkg/; entrypoint in entrypoint/)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from . import __version__
from .diff import text_to_lines, unified_diff
from .io import (
    iter_paths,
    load_documents_from_path,
    load_documents_from_stdin,
)
from .normalize import normalize_document


def _dump_yaml(doc: dict[str, Any], indent: int = 2) -> str:
    yaml = YAML()
    yaml.indent(mapping=indent, sequence=indent, offset=0)
    yaml.width = 4096
    from io import StringIO

    buf = StringIO()
    yaml.dump(doc, buf)
    return buf.getvalue()


def _dump_json(doc: dict[str, Any], indent: int = 2) -> str:
    return json.dumps(doc, sort_keys=True, indent=indent) + "\n"


def serialize(doc: dict[str, Any], fmt: str, indent: int) -> str:
    if fmt == "json":
        return _dump_json(doc, indent)
    return _dump_yaml(doc, indent)


def run(
    path_arg: str | None,
    *,
    fmt: str = "yaml",
    indent: int = 2,
    drop_status: bool = True,
    drop_managed_fields: bool = True,
    drop_last_applied: bool = True,
    drop_creation_timestamp: bool = True,
    drop_resource_version: bool = True,
    drop_uid: bool = True,
    drop_generation: bool = True,
    drop_owner_references: bool = True,
    drop_generate_name: bool = True,
    drop_node_name: bool = True,
    drop_ephemeral_containers: bool = True,
    drop_empty: bool = True,
    sort_labels: bool = False,
    sort_annotations: bool = False,
    write: bool = False,
    check: bool = False,
    diff: bool = False,
    summary: bool = False,
) -> tuple[int, int, int]:
    """
    Run normalization. Returns (exit_code, files_changed_count, docs_changed_count).
    """
    normalize_kw = dict(
        drop_status=drop_status,
        drop_managed_fields=drop_managed_fields,
        drop_last_applied=drop_last_applied,
        drop_creation_timestamp=drop_creation_timestamp,
        drop_resource_version=drop_resource_version,
        drop_uid=drop_uid,
        drop_generation=drop_generation,
        drop_owner_references=drop_owner_references,
        drop_generate_name=drop_generate_name,
        drop_node_name=drop_node_name,
        drop_ephemeral_containers=drop_ephemeral_containers,
        drop_empty=drop_empty,
        sort_labels=sort_labels,
        sort_annotations=sort_annotations,
    )

    files_changed = 0
    docs_changed = 0
    parse_errors: list[str] = []

    def process_docs(
        path: Path | None,
        doc_iter,
        original_by_path: dict[str, str],
        normalized_by_path: dict[str, str],
    ) -> None:
        nonlocal files_changed, docs_changed
        docs_orig: list[str] = []
        docs_norm: list[str] = []
        for doc_idx, doc in doc_iter:
            try:
                norm = normalize_document(doc, **normalize_kw)
                orig_text = serialize(doc, fmt, indent)
                norm_text = serialize(norm, fmt, indent)
                docs_orig.append(orig_text)
                docs_norm.append(norm_text)
                if orig_text.strip() != norm_text.strip():
                    docs_changed += 1
            except Exception as e:
                parse_errors.append(str(e))
                raise
        key = str(path) if path else "<stdin>"
        original_by_path[key] = "\n---\n".join(docs_orig)
        normalized_by_path[key] = "\n---\n".join(docs_norm)
        if original_by_path[key] != normalized_by_path[key]:
            files_changed += 1

    original_by_path: dict[str, str] = {}
    normalized_by_path: dict[str, str] = {}

    # Stdin: explicit "-" or no path with piped stdin
    use_stdin = path_arg == "-" or (path_arg is None and not sys.stdin.isatty())
    if use_stdin:
        if write:
            sys.stderr.write("error: --write is not allowed with stdin\n")
            return (2, 0, 0)
        try:
            doc_list = list(load_documents_from_stdin())
            if not doc_list:
                return (0, 0, 0)
            for _idx, doc in doc_list:
                norm = normalize_document(doc, **normalize_kw)
                sys.stdout.write(serialize(norm, fmt, indent))
                if _idx < len(doc_list) - 1:
                    sys.stdout.write("---\n")
            return (0, 0, 0)
        except Exception as e:
            sys.stderr.write(f"error: {e}\n")
            return (2, 0, 0)

    try:
        paths = list(iter_paths(path_arg))
    except FileNotFoundError as e:
        sys.stderr.write(f"error: {e}\n")
        return (2, 0, 0)
    if not paths:
        sys.stderr.write("error: no YAML/JSON files found\n")
        return (2, 0, 0)

    for path in paths:
        if not path.is_file():
            continue
        try:
            doc_iter = load_documents_from_path(path)
            process_docs(path, doc_iter, original_by_path, normalized_by_path)
        except Exception as e:
            parse_errors.append(str(e))

    if parse_errors:
        for err in parse_errors:
            sys.stderr.write(f"error: {err}\n")
        return (2, files_changed, docs_changed)

    if check:
        if docs_changed > 0:
            if summary:
                sys.stderr.write(
                    f"Files that would change: {files_changed}, documents: {docs_changed}\n"
                )
            return (1, files_changed, docs_changed)
        return (0, 0, 0)

    if diff:
        for key in sorted(original_by_path.keys()):
            a_lines = text_to_lines(original_by_path[key])
            b_lines = text_to_lines(normalized_by_path[key])
            diff_lines = unified_diff(a_lines, b_lines, fromfile=key, tofile=key)
            if diff_lines:
                sys.stdout.writelines(diff_lines)
        return (0, files_changed, docs_changed)

    if summary and (files_changed or docs_changed):
        sys.stderr.write(f"Files changed: {files_changed}, documents: {docs_changed}\n")

    if write:
        for path in paths:
            if not path.is_file():
                continue
            key = str(path)
            if key in normalized_by_path:
                path.write_text(normalized_by_path[key], encoding="utf-8")
        return (0, files_changed, docs_changed)

    for path in paths:
        if not path.is_file():
            continue
        key = str(path)
        if key in normalized_by_path:
            sys.stdout.write(normalized_by_path[key])
            if not normalized_by_path[key].endswith("\n"):
                sys.stdout.write("\n")
    return (0, files_changed, docs_changed)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kubectl-manifest-clean",
        description="Make Kubernetes manifests deterministic and diff-friendly.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="File, directory, or - for stdin",
    )
    parser.add_argument(
        "--format",
        choices=("yaml", "json"),
        default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="Indent size (default: 2)",
    )
    parser.add_argument(
        "--no-drop-status",
        action="store_false",
        dest="drop_status",
        default=True,
        help="Keep .status (default: drop)",
    )
    parser.add_argument(
        "--no-drop-managed-fields",
        action="store_false",
        dest="drop_managed_fields",
        default=True,
        help="Keep .metadata.managedFields (default: drop)",
    )
    parser.add_argument(
        "--no-drop-last-applied",
        action="store_false",
        dest="drop_last_applied",
        default=True,
        help="Keep annotation kubectl.kubernetes.io/last-applied-configuration (default: drop)",
    )
    parser.add_argument(
        "--no-drop-creation-timestamp",
        action="store_false",
        dest="drop_creation_timestamp",
        default=True,
        help="Keep .metadata.creationTimestamp (default: drop)",
    )
    parser.add_argument(
        "--no-drop-resource-version",
        action="store_false",
        dest="drop_resource_version",
        default=True,
        help="Keep .metadata.resourceVersion (default: drop)",
    )
    parser.add_argument(
        "--no-drop-uid",
        action="store_false",
        dest="drop_uid",
        default=True,
        help="Keep .metadata.uid (default: drop)",
    )
    parser.add_argument(
        "--no-drop-generation",
        action="store_false",
        dest="drop_generation",
        default=True,
        help="Keep .metadata.generation (default: drop)",
    )
    parser.add_argument(
        "--no-drop-owner-references",
        action="store_false",
        dest="drop_owner_references",
        default=True,
        help="Keep .metadata.ownerReferences (default: drop)",
    )
    parser.add_argument(
        "--no-drop-generate-name",
        action="store_false",
        dest="drop_generate_name",
        default=True,
        help="Keep .metadata.generateName (default: drop)",
    )
    parser.add_argument(
        "--no-drop-node-name",
        action="store_false",
        dest="drop_node_name",
        default=True,
        help="Keep spec.nodeName (default: drop)",
    )
    parser.add_argument(
        "--no-drop-ephemeral-containers",
        action="store_false",
        dest="drop_ephemeral_containers",
        default=True,
        help="Keep spec.ephemeralContainers (default: drop)",
    )
    parser.add_argument(
        "--no-drop-empty",
        action="store_false",
        dest="drop_empty",
        default=True,
        help="Keep empty dict/list values (default: drop)",
    )
    parser.add_argument(
        "--sort-labels",
        action="store_true",
        help="Sort .metadata.labels keys",
    )
    parser.add_argument(
        "--sort-annotations",
        action="store_true",
        help="Sort .metadata.annotations keys",
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Overwrite files in place (file/dir only)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any content would change",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Print unified diff",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show changed files and doc count",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    path_arg = args.path
    if path_arg is None and not sys.stdin.isatty():
        path_arg = "-"

    code, _, _ = run(
        path_arg,
        fmt=args.format,
        indent=args.indent,
        drop_status=args.drop_status,
        drop_managed_fields=args.drop_managed_fields,
        drop_last_applied=args.drop_last_applied,
        drop_creation_timestamp=args.drop_creation_timestamp,
        drop_resource_version=args.drop_resource_version,
        drop_uid=args.drop_uid,
        drop_generation=args.drop_generation,
        drop_owner_references=args.drop_owner_references,
        drop_generate_name=args.drop_generate_name,
        drop_node_name=args.drop_node_name,
        drop_ephemeral_containers=args.drop_ephemeral_containers,
        drop_empty=args.drop_empty,
        sort_labels=args.sort_labels,
        sort_annotations=args.sort_annotations,
        write=args.write,
        check=args.check,
        diff=args.diff,
        summary=args.summary,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
