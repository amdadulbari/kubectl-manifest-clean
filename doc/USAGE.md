# kubectl manifest-clean — Usage

## Synopsis

```text
kubectl manifest-clean [PATH|-] [flags]
```

- **PATH**: file, directory (recursive `*.yaml`, `*.yml`, `*.json`), or `-` for stdin.
- If no path is given and stdin is piped, input is read from stdin.
- Multi-document YAML (`---` separated) is supported; boundaries are preserved.

## Flags

**Defaults:** Status, managedFields, last-applied, creationTimestamp, resourceVersion, uid, and generation are **dropped by default**. Use `--no-drop-*` to keep.

| Flag | Description |
|------|-------------|
| `--format yaml\|json` | Output format (default: `yaml`) |
| `--indent N` | Indent size (default: `2`) |
| `--no-drop-status` | Keep `.status` (default: drop) |
| `--no-drop-managed-fields` | Keep `.metadata.managedFields` (default: drop) |
| `--no-drop-last-applied` | Keep last-applied-configuration annotation (default: drop) |
| `--no-drop-creation-timestamp` | Keep `.metadata.creationTimestamp` (default: drop) |
| `--no-drop-resource-version` | Keep `.metadata.resourceVersion` (default: drop) |
| `--no-drop-uid` | Keep `.metadata.uid` (default: drop) |
| `--no-drop-generation` | Keep `.metadata.generation` (default: drop) |
| `--drop-empty` | Recursively remove empty dict/list values |
| `--sort-labels` | Sort `.metadata.labels` keys |
| `--sort-annotations` | Sort `.metadata.annotations` keys |
| `-w`, `--write` | Overwrite files in place (file/dir only) |
| `--check` | Exit 1 if any content would change |
| `--diff` | Print unified diff |
| `--summary` | Show changed files and doc count |
| `--version` | Print version and exit |

## Exit codes

- **0**: Success; no changes (or changes applied with `--write`).
- **1**: `--check` detected that some content would change.
- **2**: Usage or runtime errors (e.g. invalid YAML, missing path).

## Examples

```bash
# Clean running pod YAML (noisy fields dropped by default)
kubectl get pod my-pod -o yaml | kubectl manifest-clean -

# Clean Helm output
helm template myrelease ./chart | kubectl manifest-clean -

# Normalize a directory and overwrite files
kubectl manifest-clean ./k8s -w --summary

# Check if any file would change (CI)
kubectl manifest-clean ./k8s --check

# Show unified diff
kubectl manifest-clean ./k8s --diff

# Output JSON with custom indent
kubectl manifest-clean ./deploy.yaml --format json --indent 4
```

## Notes

- Arrays/lists are **not** reordered; only dictionary keys are sorted.
- Parsing errors show filename and YAML document index.
- If a directory contains invalid YAML, other files are still processed; a summary of failures is printed and exit code is 2.
