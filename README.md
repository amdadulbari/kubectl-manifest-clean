# kubectl-manifest-clean

> Make Kubernetes manifests **deterministic** and **diff-friendly**. Canonical key sorting, strip runtime noise, optional empty pruning. Install via [Krew](https://krew.sigs.k8s.io/) or [releases](https://github.com/amdadulbari/kubectl-manifest-clean/releases).

[![CI](https://github.com/amdadulbari/kubectl-manifest-clean/actions/workflows/ci.yml/badge.svg)](https://github.com/amdadulbari/kubectl-manifest-clean/actions/workflows/ci.yml)

---

## Features

- **Deterministic output** — Recursively sort all dictionary keys so manifests are stable and Git diffs are meaningful. *Arrays are not reordered.*
- **Strip runtime noise by default** — Removes fields that change on every apply or are cluster-generated, so you see only what you’d commit.
- **Optional empty pruning** — Drops empty maps/lists (`{}`, `[]`) by default; use `--no-drop-empty` to keep.
- **CI-friendly** — `--check` (exit 1 if anything would change), `--diff`, `--summary`; works with files, directories, or stdin.

### What gets dropped by default

| Category | Fields removed (use `--no-drop-*` to keep) |
|----------|--------------------------------------------|
| **Metadata** | `status`, `managedFields`, `creationTimestamp`, `resourceVersion`, `uid`, `generation`, `ownerReferences`, `generateName`, last-applied-configuration annotation |
| **Pod / workload** | `spec.nodeName`, `spec.ephemeralContainers`, `spec.dnsPolicy`, `spec.terminationGracePeriodSeconds`, `containers[].terminationMessagePath`, `terminationMessagePolicy` |
| **Deployment** | `spec.revisionHistoryLimit`, `spec.progressDeadlineSeconds` |
| **Empty** | Empty maps and lists (e.g. `securityContext: {}`, `resources: {}`) |

---

## Why this exists

In GitOps, manifests are often touched by the cluster (status, managedFields, UIDs, timestamps) or by tools (ephemeral containers, defaults). That produces noisy Git diffs and makes real changes hard to spot. **kubectl-manifest-clean** normalizes manifests so diffs show only meaningful changes.

---

## Quick start

**Install (Krew)**

```bash
kubectl krew install manifest-clean
```

**Clean a running pod** (no flags needed; noisy fields dropped by default)

```bash
kubectl get pod my-pod -o yaml | kubectl manifest-clean -
```

**Clean Helm output**

```bash
helm template myrelease ./chart | kubectl manifest-clean -
```

**Normalize files on disk**

```bash
kubectl manifest-clean ./k8s -w --summary
```

---

## Installation

### Krew

After [installing Krew](https://krew.sigs.k8s.io/docs/user-guide/setup/install/):

```bash
kubectl krew install manifest-clean
```

To install from the repo before it’s in krew-index:

```bash
kubectl krew install --manifest=deploy/krew/plugin.yaml
```

**Uninstall / reinstall**

```bash
kubectl krew uninstall manifest-clean
kubectl krew install manifest-clean
# or: kubectl krew install --manifest=deploy/krew/plugin.yaml
```

### Direct download

Download the binary for your platform from [Releases](https://github.com/amdadulbari/kubectl-manifest-clean/releases) and put it on your `PATH` as `kubectl-manifest-clean` (or `kubectl-manifest-clean.exe` on Windows).

---

## Usage

```bash
kubectl manifest-clean [PATH|-] [flags]
```

- **PATH** — File, directory (recursive `*.yaml`, `*.yml`, `*.json`), or `-` for stdin.
- If no path is given and stdin is piped, input is read from stdin.
- Multi-document YAML (`---`) is supported; boundaries are preserved.

### Examples

| Goal | Command |
|------|--------|
| Clean running pod | `kubectl get pod my-pod -o yaml \| kubectl manifest-clean -` |
| Clean Helm output | `helm template myrelease ./chart \| kubectl manifest-clean -` |
| Normalize dir (in place) | `kubectl manifest-clean ./k8s -w --summary` |
| CI: fail if dirty | `kubectl manifest-clean ./k8s --check` |
| Show diff | `kubectl manifest-clean ./k8s --diff` |
| JSON, 4 spaces | `kubectl manifest-clean ./deploy.yaml --format json --indent 4` |

### Flags

**Output**

| Flag | Description |
|------|-------------|
| `--format yaml\|json` | Output format (default: `yaml`) |
| `--indent N` | Indent size (default: `2`) |

**What to drop (all dropped by default; use `--no-drop-*` to keep)**

| Flag | Keeps |
|------|--------|
| `--no-drop-status` | `.status` |
| `--no-drop-managed-fields` | `.metadata.managedFields` |
| `--no-drop-last-applied` | last-applied-configuration annotation |
| `--no-drop-creation-timestamp` | `.metadata.creationTimestamp` |
| `--no-drop-resource-version` | `.metadata.resourceVersion` |
| `--no-drop-uid` | `.metadata.uid` |
| `--no-drop-generation` | `.metadata.generation` |
| `--no-drop-owner-references` | `.metadata.ownerReferences` |
| `--no-drop-generate-name` | `.metadata.generateName` |
| `--no-drop-node-name` | `spec.nodeName` |
| `--no-drop-ephemeral-containers` | `spec.ephemeralContainers` |
| `--no-drop-dns-policy` | `spec.dnsPolicy` |
| `--no-drop-termination-grace-period-seconds` | `spec.terminationGracePeriodSeconds` |
| `--no-drop-revision-history-limit` | `spec.revisionHistoryLimit` |
| `--no-drop-progress-deadline-seconds` | `spec.progressDeadlineSeconds` |
| `--no-drop-termination-message` | `containers[].terminationMessagePath/Policy` |
| `--no-drop-empty` | Empty dict/list (e.g. `securityContext: {}`) |

**Other**

| Flag | Description |
|------|-------------|
| `--sort-labels` | Sort `.metadata.labels` keys |
| `--sort-annotations` | Sort `.metadata.annotations` keys |
| `-w`, `--write` | Overwrite files in place (file/dir only) |
| `--check` | Exit 1 if any content would change |
| `--diff` | Print unified diff |
| `--summary` | Show changed file and doc counts |
| `--version` | Print version |

### Exit codes

| Code | Meaning |
|------|--------|
| **0** | Success (no changes, or changes applied with `--write`) |
| **1** | `--check` detected that some content would change |
| **2** | Usage or runtime error (e.g. invalid YAML, missing path) |

---

## Building from source

**Requirements:** Python 3.11+, pip

```bash
git clone https://github.com/amdadulbari/kubectl-manifest-clean.git
cd kubectl-manifest-clean
pip install -e ".[dev]"
kubectl manifest-clean --help
```

**Single-file binary (PyInstaller)**

```bash
pip install pyinstaller
pyinstaller -F -n kubectl-manifest-clean -p . entrypoint/manifest_clean/main.py
```

Binary is written to `dist/kubectl-manifest-clean` (or `dist/kubectl-manifest-clean.exe` on Windows).

---

## Creating a release

1. **Tag and push** (triggers the release workflow):

   ```bash
   git push origin main
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **GitHub Actions** builds Linux (amd64, arm64), macOS (arm64), and Windows (amd64) and publishes a GitHub Release with archives and `checksums.txt`.

3. **Krew:** Copy SHA256 hashes from `checksums.txt` into `deploy/krew/plugin.yaml`, then submit that manifest to [krew-index](https://github.com/kubernetes-sigs/krew-index) (e.g. as `plugins/manifest-clean.yaml`).

---

## Repository layout

| Path | Purpose |
|------|---------|
| `entrypoint/manifest_clean/` | CLI entrypoint |
| `pkg/manifest_clean/` | Core logic (normalize, io, diff, cli) |
| `deploy/krew/` | Krew plugin manifest |
| `doc/` | Usage docs |
| `.github/workflows/ci.yml` | Tests and lint on push/PR |
| `.github/workflows/release.yml` | Build and release on tag `v*.*.*` |
| `tests/` | Pytest suite |

---

## License

Apache-2.0. See [LICENSE](LICENSE).
