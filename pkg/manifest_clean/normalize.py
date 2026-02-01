"""Canonical normalization of Kubernetes manifest structures."""

from __future__ import annotations

from typing import Any

LAST_APPLIED_KEY = "kubectl.kubernetes.io/last-applied-configuration"


def is_kubernetes_like(obj: dict[str, Any]) -> bool:
    """Return True if obj looks like a Kubernetes resource (has apiVersion and kind)."""
    return isinstance(obj, dict) and "apiVersion" in obj and "kind" in obj


def prune_noisy_fields(
    obj: dict[str, Any],
    *,
    drop_status: bool = False,
    drop_managed_fields: bool = False,
    drop_last_applied: bool = False,
    drop_creation_timestamp: bool = False,
    drop_resource_version: bool = False,
    drop_uid: bool = False,
    drop_generation: bool = False,
) -> None:
    """Mutate obj in place, removing noisy fields (only on K8s-like objects)."""
    if not is_kubernetes_like(obj):
        return

    if drop_status and "status" in obj:
        del obj["status"]

    metadata = obj.get("metadata")
    if not isinstance(metadata, dict):
        return

    if drop_managed_fields and "managedFields" in metadata:
        del metadata["managedFields"]
    if drop_creation_timestamp and "creationTimestamp" in metadata:
        del metadata["creationTimestamp"]
    if drop_resource_version and "resourceVersion" in metadata:
        del metadata["resourceVersion"]
    if drop_uid and "uid" in metadata:
        del metadata["uid"]
    if drop_generation and "generation" in metadata:
        del metadata["generation"]

    if drop_last_applied:
        ann = metadata.get("annotations")
        if isinstance(ann, dict) and LAST_APPLIED_KEY in ann:
            del ann[LAST_APPLIED_KEY]


def drop_empty_recursive(obj: Any) -> Any:
    """
    Return a copy of obj with empty dict/list values removed.
    Do NOT remove 0, False, or empty strings.
    """
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            v_clean = drop_empty_recursive(v)
            if (isinstance(v_clean, dict) and len(v_clean) == 0) or (
                isinstance(v_clean, list) and len(v_clean) == 0
            ):
                continue
            result[k] = v_clean
        return result
    if isinstance(obj, list):
        return [drop_empty_recursive(item) for item in obj]
    return obj


def _drop_empty_in_place(obj: Any) -> bool:
    """
    Mutate obj in place, removing keys whose value is {} or [].
    Returns True if something was removed (caller may want to re-run on dicts).
    """
    if isinstance(obj, dict):
        to_del = [
            k
            for k, v in obj.items()
            if (isinstance(v, dict) and len(v) == 0)
            or (isinstance(v, list) and len(v) == 0)
        ]
        for k in to_del:
            del obj[k]
        for v in obj.values():
            _drop_empty_in_place(v)
        return len(to_del) > 0
    if isinstance(obj, list):
        for item in obj:
            _drop_empty_in_place(item)
    return False


def drop_empty_in_place(obj: Any) -> None:
    """Recursively remove empty dict/list values in place. Run until no change."""
    while _drop_empty_in_place(obj):
        pass


def sort_dict_keys(obj: Any) -> Any:
    """Return a new structure with all dict keys sorted lexicographically. Arrays unchanged."""
    if isinstance(obj, dict):
        return {k: sort_dict_keys(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [sort_dict_keys(item) for item in obj]
    return obj


def sort_labels_and_annotations(obj: dict[str, Any]) -> None:
    """Ensure metadata.labels and metadata.annotations have deterministic key order (mutate in place)."""
    if not is_kubernetes_like(obj):
        return
    metadata = obj.get("metadata")
    if not isinstance(metadata, dict):
        return
    for key in ("labels", "annotations"):
        if key not in metadata or not isinstance(metadata[key], dict):
            continue
        metadata[key] = dict(sorted(metadata[key].items()))


def normalize_document(
    doc: dict[str, Any],
    *,
    drop_status: bool = False,
    drop_managed_fields: bool = False,
    drop_last_applied: bool = False,
    drop_creation_timestamp: bool = False,
    drop_resource_version: bool = False,
    drop_uid: bool = False,
    drop_generation: bool = False,
    drop_empty: bool = False,
    sort_labels: bool = False,
    sort_annotations: bool = False,
) -> dict[str, Any]:
    """
    Normalize a single document: prune fields, optionally drop empty, then sort keys.
    Returns a new dict; does not mutate doc.
    """
    import copy

    obj = copy.deepcopy(doc)

    prune_noisy_fields(
        obj,
        drop_status=drop_status,
        drop_managed_fields=drop_managed_fields,
        drop_last_applied=drop_last_applied,
        drop_creation_timestamp=drop_creation_timestamp,
        drop_resource_version=drop_resource_version,
        drop_uid=drop_uid,
        drop_generation=drop_generation,
    )

    if drop_empty:
        drop_empty_in_place(obj)

    if sort_labels or sort_annotations:
        sort_labels_and_annotations(obj)

    return sort_dict_keys(obj)
