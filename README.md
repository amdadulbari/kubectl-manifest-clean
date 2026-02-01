# kubectl-manifest-clean

A **kubectl** plugin that makes Kubernetes manifests deterministic and diff-friendly by canonical sorting of keys, removing noisy runtime fields, and optionally pruning empty structures. Installable via [Krew](https://krew.sigs.k8s.io/).

## What it does

- **Canonical sorting** of dictionary keys (recursively), so manifest order is stable and Git diffs are meaningful.
- **Removes noisy fields** that break Git diffs: `status`, `managedFields`, `creationTimestamp`, `resourceVersion`, `uid`, `generation`, and the `kubectl.kubernetes.io/last-applied-configuration` annotation.
- **Optional cleanup**: recursively remove empty maps/lists (`{}`, `[]`), and sort `metadata.labels` and `metadata.annotations` for deterministic output.

**Important:** Arrays/lists are **not** reordered; only dictionary keys are sorted.

## Why this exists

In GitOps workflows, manifests are often generated or applied by tools that add runtime metadata (`status`, `managedFields`, timestamps, UIDs). That causes noisy Git diffs and makes it hard to see real changes. Normalizing manifests with `kubectl manifest-clean` reduces diff noise and keeps repositories readable.

## Installation

### Krew

After [installing Krew](https://krew.sigs.k8s.io/docs/user-guide/setup/install/), add the plugin from the [krew-index](https://github.com/kubernetes-sigs/krew-index) (once submitted):

```bash
kubectl krew install manifest-clean
```

To test before submission, install from a local manifest:

```bash
kubectl krew install --manifest=deploy/krew/plugin.yaml
```

(Update `deploy/krew/plugin.yaml` with your repo URL and release checksums first.)

### Direct download

Download the binary for your platform from the [Releases](https://github.com/YOUR_ORG/kubectl-manifest-clean/releases) page and place it on your `PATH` as `kubectl-manifest-clean` (or `kubectl-manifest-clean.exe` on Windows).

## Usage

```bash
kubectl manifest-clean [PATH|-] [flags]
```

- **PATH**: file, directory (recursive `*.yaml`, `*.yml`, `*.json`), or `-` for stdin.
- If no path is given and stdin is piped, input is read from stdin.
- Multi-document YAML (`---` separated) is supported; boundaries are preserved.

### Examples

**Clean Helm output and drop common noisy fields:**

```bash
helm template myrelease ./chart | kubectl manifest-clean - --drop-status --drop-managed-fields --drop-last-applied
```

**Normalize a directory and overwrite files:**

```bash
kubectl manifest-clean ./k8s -w --summary
```

**Check if any file would change (CI):**

```bash
kubectl manifest-clean ./k8s --check
```

**Show a unified diff:**

```bash
kubectl manifest-clean ./k8s --diff
```

**Output JSON with custom indent:**

```bash
kubectl manifest-clean ./deploy.yaml --format json --indent 4
```

### Flags

| Flag | Description |
|------|-------------|
| `--format yaml\|json` | Output format (default: `yaml`) |
| `--indent N` | Indent size (default: `2`) |
| `--drop-status` | Remove `.status` |
| `--drop-managed-fields` | Remove `.metadata.managedFields` |
| `--drop-last-applied` | Remove annotation `kubectl.kubernetes.io/last-applied-configuration` |
| `--drop-creation-timestamp` | Remove `.metadata.creationTimestamp` |
| `--drop-resource-version` | Remove `.metadata.resourceVersion` |
| `--drop-uid` | Remove `.metadata.uid` |
| `--drop-generation` | Remove `.metadata.generation` |
| `--drop-empty` | Recursively remove empty dict/list values |
| `--sort-labels` | Sort `.metadata.labels` keys |
| `--sort-annotations` | Sort `.metadata.annotations` keys |
| `-w`, `--write` | Overwrite files in place (file/dir only) |
| `--check` | Exit 1 if any content would change |
| `--diff` | Print unified diff |
| `--summary` | Show changed files and doc count |

### Exit codes

- **0**: Success; no changes (or changes applied with `--write`).
- **1**: `--check` detected that some content would change.
- **2**: Usage or runtime errors (e.g. invalid YAML, missing path).

## Building from source

- **Python 3.11+** and `pip` are required.

```bash
git clone https://github.com/YOUR_ORG/kubectl-manifest-clean.git
cd kubectl-manifest-clean
pip install -e ".[dev]"
kubectl manifest-clean --help
```

### Single-file binary (PyInstaller)

```bash
pip install pyinstaller
pyinstaller -F -n kubectl-manifest-clean -m manifest_clean.cli
```

The binary is produced in `dist/kubectl-manifest-clean` (or `dist/kubectl-manifest-clean.exe` on Windows). Run this on each target OS/arch for cross-platform releases; the GitHub Actions workflow does this on tag push.

## Repository layout

- **`entrypoint/manifest_clean/`** – Entrypoint (template’s `cmd/plugin/`): `main.py` invokes the plugin.
- **`pkg/manifest_clean/`** – Plugin logic (template’s `pkg/plugin/`): `cli`, `normalize`, `io`, `diff`.
- **`deploy/krew/`** – Krew plugin manifest (for krew-index).
- **`doc/`** – Usage documentation (e.g. `doc/USAGE.md`).
- **`.github/workflows/ci.yml`** – Run tests and lint on push/PR.
- **`.github/workflows/release.yml`** – Build and release on tag push `v*.*.*`.
- **`tests/`** – Pytest test suite (normalize, io, diff, cli).

## License

Apache-2.0. See [LICENSE](LICENSE).
