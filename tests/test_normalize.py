"""Tests for manifest_clean.normalize."""

import pytest

from pkg.manifest_clean.normalize import (
    LAST_APPLIED_KEY,
    drop_empty_in_place,
    drop_empty_recursive,
    is_kubernetes_like,
    normalize_document,
    prune_noisy_fields,
    sort_dict_keys,
    sort_labels_and_annotations,
)


def test_is_kubernetes_like():
    assert is_kubernetes_like({"apiVersion": "v1", "kind": "Pod"}) is True
    assert is_kubernetes_like({"kind": "Pod"}) is False
    assert is_kubernetes_like({"apiVersion": "v1"}) is False
    assert is_kubernetes_like({}) is False
    assert is_kubernetes_like("not a dict") is False


def test_sort_dict_keys():
    obj = {"b": 2, "a": 1}
    got = sort_dict_keys(obj)
    assert list(got.keys()) == ["a", "b"]
    assert sort_dict_keys([3, 1, 2]) == [3, 1, 2]  # lists unchanged


def test_sort_dict_keys_nested():
    obj = {"z": {"y": 1, "x": 2}, "a": []}
    got = sort_dict_keys(obj)
    assert list(got.keys()) == ["a", "z"]
    assert list(got["z"].keys()) == ["x", "y"]


def test_normalize_document_drops_status():
    doc = {"apiVersion": "v1", "kind": "Pod", "status": {"phase": "Running"}}
    out = normalize_document(doc, drop_status=True)
    assert "status" not in out
    assert doc["status"] == {"phase": "Running"}  # original unchanged


def test_normalize_document_sorts_keys():
    doc = {"kind": "Pod", "apiVersion": "v1"}
    out = normalize_document(doc)
    assert list(out.keys()) == ["apiVersion", "kind"]


def test_prune_noisy_fields_drop_managed_fields():
    doc = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": "x", "managedFields": [{}]},
    }
    prune_noisy_fields(doc, drop_managed_fields=True)
    assert "managedFields" not in doc["metadata"]


def test_prune_noisy_fields_drop_last_applied():
    doc = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "x",
            "annotations": {LAST_APPLIED_KEY: "{}", "other": "ok"},
        },
    }
    prune_noisy_fields(doc, drop_last_applied=True)
    assert LAST_APPLIED_KEY not in doc["metadata"]["annotations"]
    assert doc["metadata"]["annotations"]["other"] == "ok"


def test_prune_noisy_fields_skips_non_k8s():
    doc = {"foo": "bar", "metadata": {"uid": "123"}}
    prune_noisy_fields(doc, drop_uid=True)
    assert doc["metadata"]["uid"] == "123"  # unchanged


def test_drop_empty_recursive():
    obj = {"a": 1, "b": {}, "c": [], "d": {"x": {}}}
    got = drop_empty_recursive(obj)
    assert got == {"a": 1}
    assert "b" not in got
    assert "c" not in got
    assert "d" not in got


def test_drop_empty_recursive_preserves_zero_and_false():
    obj = {"a": 0, "b": False, "c": ""}
    got = drop_empty_recursive(obj)
    assert got["a"] == 0
    assert got["b"] is False
    assert got["c"] == ""


def test_drop_empty_in_place():
    obj = {"a": 1, "b": {}, "c": []}
    drop_empty_in_place(obj)
    assert obj == {"a": 1}


def test_normalize_document_drop_empty():
    doc = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "x", "labels": {}}}
    out = normalize_document(doc, drop_empty=True)
    assert "labels" not in out.get("metadata", {})


def test_sort_labels_and_annotations():
    doc = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": "x", "labels": {"z": "1", "a": "2"}, "annotations": {"y": "1", "b": "2"}},
    }
    sort_labels_and_annotations(doc)
    assert list(doc["metadata"]["labels"].keys()) == ["a", "z"]
    assert list(doc["metadata"]["annotations"].keys()) == ["b", "y"]


def test_sort_labels_and_annotations_skips_non_k8s():
    doc = {"metadata": {"labels": {"z": "1"}}}
    sort_labels_and_annotations(doc)
    assert list(doc["metadata"]["labels"].keys()) == ["z"]  # unchanged order for non-k8s
