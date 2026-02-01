"""
Entrypoint for kubectl-manifest-clean (entrypoint/ = template cmd/plugin).

Delegates to pkg.manifest_clean.cli.main().
"""

from pkg.manifest_clean.cli import main

if __name__ == "__main__":
    main()
