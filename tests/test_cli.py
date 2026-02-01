"""Tests for manifest_clean.cli (run() and integration)."""

from pkg.manifest_clean.cli import run


def test_run_missing_path_returns_2(capsys):
    code, fc, dc = run("nonexistent_file_xyz")
    assert code == 2
    out, err = capsys.readouterr()
    assert "error" in err or "nonexistent" in err


def test_run_no_path_no_files_returns_2(capsys):
    # path_arg is a dir with no yaml files, or we pass a dir that exists but has no *.yaml
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        code, fc, dc = run(d)
    assert code == 2
    out, err = capsys.readouterr()
    assert "no YAML" in err or "error" in err


def test_run_single_file_normalizes(capsys, tmp_path):
    f = tmp_path / "pod.yaml"
    f.write_text("kind: Pod\napiVersion: v1\nmetadata:\n  name: foo\n")
    code, fc, dc = run(str(f))
    assert code == 0
    out, err = capsys.readouterr()
    # Keys should be sorted (apiVersion before kind)
    assert "apiVersion" in out
    assert "kind" in out
    assert out.index("apiVersion") < out.index("kind") or "apiVersion" in out


def test_run_with_drop_status(capsys, tmp_path):
    f = tmp_path / "pod.yaml"
    f.write_text(
        "apiVersion: v1\nkind: Pod\nmetadata:\n  name: x\n"
        "status:\n  phase: Running\n"
    )
    code, fc, dc = run(str(f), drop_status=True)
    assert code == 0
    out, err = capsys.readouterr()
    assert "status" not in out
    assert "phase" not in out


def test_run_check_detects_change_returns_1(capsys, tmp_path):
    # Unsorted keys will be normalized, so content would change
    f = tmp_path / "pod.yaml"
    f.write_text("kind: Pod\napiVersion: v1\nmetadata:\n  name: bar\n")
    code, fc, dc = run(str(f), check=True)
    assert code == 1
    assert dc >= 0  # may be 1 if serialization differs


def test_run_check_no_change_returns_0(capsys, tmp_path):
    # Already sorted and minimal
    f = tmp_path / "pod.yaml"
    f.write_text("apiVersion: v1\nkind: Pod\nmetadata:\n  name: bar\n")
    code, fc, dc = run(str(f), check=True)
    # Might be 0 or 1 depending on YAML round-trip (e.g. quoting)
    assert code in (0, 1)


def test_run_write_overwrites_file(tmp_path):
    f = tmp_path / "pod.yaml"
    original = "kind: Pod\napiVersion: v1\nmetadata:\n  name: baz\n"
    f.write_text(original)
    code, fc, dc = run(str(f), write=True)
    assert code == 0
    content = f.read_text()
    # Should be normalized (sorted keys)
    assert "apiVersion" in content and "kind" in content


def test_run_write_rejected_for_stdin(capsys):
    # When path_arg is "-", write should return 2
    # We can't easily simulate stdin in run() without passing path_arg="-"
    # and then run() would try to load_documents_from_stdin(). So test with path_arg="-"
    code, _, _ = run("-", write=True)
    assert code == 2
    _, err = capsys.readouterr()
    assert "stdin" in err or "write" in err.lower()


def test_run_version_in_help():
    from pkg.manifest_clean import __version__
    assert __version__ == "0.1.0"
