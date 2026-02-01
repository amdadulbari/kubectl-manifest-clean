"""Tests for manifest_clean.io."""

from io import StringIO

import pytest  # used for pytest.raises

from pkg.manifest_clean.io import (
    iter_paths,
    load_documents_from_path,
    load_documents_from_stdin,
)


def test_iter_paths_none_returns_nothing():
    assert list(iter_paths(None)) == []
    assert list(iter_paths("-")) == []


def test_iter_paths_missing_raises():
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        list(iter_paths("nonexistent"))


def test_iter_paths_single_file(tmp_path):
    f = tmp_path / "app.yaml"
    f.write_text("apiVersion: v1\nkind: ConfigMap\n")
    paths = list(iter_paths(str(tmp_path / "app.yaml")))
    assert len(paths) == 1
    assert paths[0].name == "app.yaml"


def test_iter_paths_directory_recursive(tmp_path):
    (tmp_path / "a.yaml").write_text("{}")
    (tmp_path / "b.yml").write_text("{}")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.json").write_text("{}")
    paths = list(iter_paths(str(tmp_path)))
    names = {p.name for p in paths}
    assert names == {"a.yaml", "b.yml", "c.json"}


def test_load_documents_from_path_single_doc(tmp_path):
    f = tmp_path / "doc.yaml"
    f.write_text("apiVersion: v1\nkind: Pod\nmetadata:\n  name: foo\n")
    docs = list(load_documents_from_path(f))
    assert len(docs) == 1
    idx, doc = docs[0]
    assert idx == 0
    assert doc["kind"] == "Pod"
    assert doc["metadata"]["name"] == "foo"


def test_load_documents_from_path_multi_doc(tmp_path):
    f = tmp_path / "multi.yaml"
    f.write_text(
        "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: a\n"
        "---\n"
        "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: b\n"
    )
    docs = list(load_documents_from_path(f))
    assert len(docs) == 2
    assert docs[0][1]["metadata"]["name"] == "a"
    assert docs[1][1]["metadata"]["name"] == "b"


def test_load_documents_from_path_invalid_yaml_raises(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("not: valid: yaml: here\n")
    with pytest.raises(Exception) as exc_info:
        list(load_documents_from_path(f))
    assert (
        "bad.yaml" in str(exc_info.value) or "document" in str(exc_info.value).lower()
    )


def test_load_documents_from_path_non_mapping_doc_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(ValueError, match="mapping"):
        list(load_documents_from_path(f))


def test_load_documents_from_stdin(monkeypatch):
    stdin = StringIO("apiVersion: v1\nkind: Pod\nmetadata:\n  name: x\n")
    monkeypatch.setattr("sys.stdin", stdin)
    docs = list(load_documents_from_stdin())
    assert len(docs) == 1
    assert docs[0][1]["metadata"]["name"] == "x"


def test_load_documents_from_path_skips_non_yaml_ext(tmp_path):
    # .txt should not be yielded by iter_paths; if we call load_documents_from_path
    # on a .txt we get nothing (suffix check)
    f = tmp_path / "readme.txt"
    f.write_text("hello")
    # iter_paths only yields .yaml, .yml, .json so we wouldn't get readme.txt.
    # Direct call to load_documents_from_path with .txt path yields nothing
    docs = list(load_documents_from_path(f))
    assert len(docs) == 0
