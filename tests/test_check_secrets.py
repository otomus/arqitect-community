"""Comprehensive tests for scripts/check_secrets.py."""

import os
import sys
import textwrap

import pytest

# Ensure the scripts package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.check_secrets import (
    ABS_PATH_PATTERNS,
    SECRET_PATTERNS,
    check_file,
    check_forbidden,
    find_pattern_violations,
    iter_files,
    main,
    read_text,
    scan_directory,
)


# ---------------------------------------------------------------------------
# A. find_pattern_violations
# ---------------------------------------------------------------------------

class TestFindPatternViolations:
    """Tests for find_pattern_violations."""

    def test_openai_key(self):
        content = "key = sk-abcdefghijklmnopqrstuvwxyz"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert len(violations) == 1
        assert "OpenAI/Stripe secret key" in violations[0]

    def test_github_token(self):
        token = "ghp_" + "A" * 36
        content = f"token = {token}"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("GitHub personal access token" in v for v in violations)

    def test_aws_access_key(self):
        content = "aws_key = AKIAIOSFODNN7EXAMPLE"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("AWS access key ID" in v for v in violations)

    def test_bearer_token(self):
        content = "Authorization: Bearer eyJhbGciOi.something+extra/value="
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Bearer token" in v for v in violations)

    def test_private_key(self):
        content = "-----BEGIN PRIVATE KEY-----"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Private key" in v for v in violations)

    def test_rsa_private_key(self):
        content = "-----BEGIN RSA PRIVATE KEY-----"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Private key" in v for v in violations)

    def test_mongodb_uri(self):
        content = 'uri = "mongodb://admin:secretpass@host:27017/db"'
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Database connection string" in v for v in violations)

    def test_postgres_uri(self):
        content = "postgres://user:pass@localhost:5432/mydb"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Database connection string" in v for v in violations)

    def test_api_key_assignment(self):
        content = 'api_key = "ABCDEFGHIJKLMNOP1234"'
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("API key assignment" in v for v in violations)

    def test_password_assignment(self):
        content = 'password = "supersecret123"'
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Secret/password assignment" in v for v in violations)

    def test_secret_assignment(self):
        content = 'secret = "longenoughvalue"'
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert any("Secret/password assignment" in v for v in violations)

    # Absolute-path patterns

    def test_macos_abs_path(self):
        content = "/Users/foo/project/file.txt"
        violations = find_pattern_violations(content, ABS_PATH_PATTERNS, "f.py")
        assert any("macOS absolute path" in v for v in violations)

    def test_linux_abs_path(self):
        content = "/home/bar/work/data.csv"
        violations = find_pattern_violations(content, ABS_PATH_PATTERNS, "f.py")
        assert any("Linux absolute path" in v for v in violations)

    def test_windows_abs_path(self):
        content = r"C:\Users\baz\Documents\file.txt"
        violations = find_pattern_violations(content, ABS_PATH_PATTERNS, "f.py")
        assert any("Windows absolute path" in v for v in violations)

    # Truncation

    def test_truncation_default(self):
        long_key = "sk-" + "A" * 80
        content = long_key
        violations = find_pattern_violations(
            content, SECRET_PATTERNS, "f.py", truncate=40, suffix="..."
        )
        assert len(violations) == 1
        # The matched text should be truncated to 40 chars followed by "..."
        assert "..." in violations[0]
        # Extract the parenthesised portion: (match...)
        paren_content = violations[0].split("(")[1].rstrip(")")
        assert paren_content == long_key[:40] + "..."

    def test_truncation_short_match_no_loss(self):
        """A match shorter than the truncate limit should appear in full."""
        content = "sk-" + "B" * 20  # 23 chars total, well under 40
        violations = find_pattern_violations(
            content, SECRET_PATTERNS, "f.py", truncate=40, suffix="..."
        )
        assert len(violations) == 1
        paren_content = violations[0].split("(")[1].rstrip(")")
        assert paren_content == content + "..."

    def test_no_suffix(self):
        content = "/Users/someone/path"
        violations = find_pattern_violations(
            content, ABS_PATH_PATTERNS, "f.py", truncate=60, suffix=""
        )
        assert len(violations) == 1
        assert violations[0].endswith(")")

    def test_clean_content_returns_empty(self):
        content = "just some normal text with no secrets"
        violations = find_pattern_violations(content, SECRET_PATTERNS, "f.py")
        assert violations == []


# ---------------------------------------------------------------------------
# B. check_forbidden
# ---------------------------------------------------------------------------

class TestCheckForbidden:

    def test_env_file_flagged(self):
        violations = check_forbidden("/some/path/.env")
        assert len(violations) == 1
        assert "FORBIDDEN FILE" in violations[0]

    def test_credentials_json_flagged(self):
        violations = check_forbidden("/repo/credentials.json")
        assert len(violations) == 1
        assert "FORBIDDEN FILE" in violations[0]

    def test_pem_extension_flagged(self):
        violations = check_forbidden("/certs/server.pem")
        assert len(violations) == 1
        assert "FORBIDDEN FILE" in violations[0]

    def test_key_extension_flagged(self):
        violations = check_forbidden("/certs/server.key")
        assert len(violations) == 1
        assert "FORBIDDEN FILE" in violations[0]

    def test_normal_json_passes(self):
        violations = check_forbidden("/repo/config/normal.json")
        assert violations == []

    def test_normal_py_passes(self):
        violations = check_forbidden("/repo/main.py")
        assert violations == []


# ---------------------------------------------------------------------------
# C. read_text
# ---------------------------------------------------------------------------

class TestReadText:

    def test_valid_utf8(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world", encoding="utf-8")
        assert read_text(str(f)) == "hello world"

    def test_binary_file_returns_content_with_errors_ignore(self, tmp_path):
        """Binary files are read with errors='ignore', so they return a string (not None)."""
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x80\x81\x82\xff\xfe")
        result = read_text(str(f))
        # errors="ignore" means it will return a (possibly empty) string, not None
        assert result is not None

    def test_nonexistent_file_returns_none(self):
        result = read_text("/nonexistent/path/file.txt")
        assert result is None

    def test_directory_returns_none(self, tmp_path):
        result = read_text(str(tmp_path))
        assert result is None


# ---------------------------------------------------------------------------
# D. check_file
# ---------------------------------------------------------------------------

class TestCheckFile:

    def test_forbidden_file_short_circuits(self, tmp_path):
        """A forbidden file should return the forbidden violation even if it also contains secrets."""
        env = tmp_path / ".env"
        env.write_text('SECRET_KEY="sk-abcdefghijklmnopqrstuvwxyz"', encoding="utf-8")
        violations = check_file(str(env))
        assert len(violations) == 1
        assert "FORBIDDEN FILE" in violations[0]

    def test_file_with_secret_detected(self, tmp_path):
        f = tmp_path / "config.py"
        f.write_text('api_key = "ABCDEFGHIJKLMNOP1234"', encoding="utf-8")
        violations = check_file(str(f))
        assert len(violations) >= 1
        assert any("API key assignment" in v for v in violations)

    def test_clean_file_returns_empty(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text("print('hello world')", encoding="utf-8")
        violations = check_file(str(f))
        assert violations == []

    def test_file_with_abs_path(self, tmp_path):
        f = tmp_path / "paths.py"
        f.write_text('base = "/Users/foo/project"', encoding="utf-8")
        violations = check_file(str(f))
        assert len(violations) >= 1
        assert any("macOS absolute path" in v for v in violations)

    def test_unreadable_file_returns_empty(self, tmp_path):
        """A file that cannot be read (e.g. OSError) should produce no violations."""
        f = tmp_path / "gone.txt"
        # File does not exist, so read_text returns None
        violations = check_file(str(f))
        assert violations == []


# ---------------------------------------------------------------------------
# E. iter_files
# ---------------------------------------------------------------------------

class TestIterFiles:

    def test_skips_git_dir(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("hi", encoding="utf-8")

        files = list(iter_files(str(tmp_path)))
        assert any("readme.txt" in f for f in files)
        assert not any(".git" in f for f in files)

    def test_skips_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "package.json").write_text("{}", encoding="utf-8")
        (tmp_path / "index.js").write_text("// ok", encoding="utf-8")

        files = list(iter_files(str(tmp_path)))
        assert any("index.js" in f for f in files)
        # Ensure no yielded file lives inside the node_modules subdirectory
        nm_prefix = str(nm) + os.sep
        assert not any(f.startswith(nm_prefix) for f in files)

    def test_skips_hidden_dirs(self, tmp_path):
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.txt").write_text("s", encoding="utf-8")
        (tmp_path / "visible.txt").write_text("v", encoding="utf-8")

        files = list(iter_files(str(tmp_path)))
        assert any("visible.txt" in f for f in files)
        assert not any(".hidden" in f for f in files)

    def test_yields_files_recursively(self, tmp_path):
        sub = tmp_path / "a" / "b" / "c"
        sub.mkdir(parents=True)
        (sub / "deep.txt").write_text("deep", encoding="utf-8")
        (tmp_path / "top.txt").write_text("top", encoding="utf-8")

        files = list(iter_files(str(tmp_path)))
        basenames = [os.path.basename(f) for f in files]
        assert "deep.txt" in basenames
        assert "top.txt" in basenames


# ---------------------------------------------------------------------------
# F. scan_directory
# ---------------------------------------------------------------------------

class TestScanDirectory:

    def test_mixed_clean_and_dirty(self, tmp_path):
        clean = tmp_path / "clean.py"
        clean.write_text("x = 42", encoding="utf-8")

        dirty = tmp_path / "dirty.py"
        dirty.write_text('api_key = "ABCDEFGHIJKLMNOP1234"', encoding="utf-8")

        violations = scan_directory(str(tmp_path))
        assert len(violations) >= 1
        assert any("dirty.py" in v for v in violations)
        assert not any("clean.py" in v for v in violations)

    def test_all_clean_returns_empty(self, tmp_path):
        (tmp_path / "a.py").write_text("print(1)", encoding="utf-8")
        (tmp_path / "b.py").write_text("print(2)", encoding="utf-8")
        violations = scan_directory(str(tmp_path))
        assert violations == []

    def test_forbidden_file_in_subdir(self, tmp_path):
        sub = tmp_path / "config"
        sub.mkdir()
        (sub / ".env").write_text("SECRET=foo", encoding="utf-8")

        violations = scan_directory(str(tmp_path))
        assert any("FORBIDDEN FILE" in v for v in violations)


# ---------------------------------------------------------------------------
# G. main() CLI
# ---------------------------------------------------------------------------

class TestMain:

    def test_no_violations_exits_0(self, tmp_path, monkeypatch):
        clean = tmp_path / "ok.py"
        clean.write_text("x = 1", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["check_secrets.py", str(tmp_path)])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_violations_exits_1(self, tmp_path, monkeypatch):
        dirty = tmp_path / "leak.py"
        dirty.write_text('password = "very_secret_password"', encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["check_secrets.py", str(tmp_path)])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_defaults_to_cwd(self, tmp_path, monkeypatch):
        """With no args, main() scans the current working directory."""
        (tmp_path / "safe.txt").write_text("nothing here", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["check_secrets.py"])
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_single_file_argument(self, tmp_path, monkeypatch):
        f = tmp_path / "single.py"
        f.write_text("sk-" + "X" * 30, encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["check_secrets.py", str(f)])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_output_on_violation(self, tmp_path, monkeypatch, capsys):
        dirty = tmp_path / "bad.py"
        dirty.write_text("AKIAIOSFODNN7EXAMPLE", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["check_secrets.py", str(tmp_path)])

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "SECRET SCAN FAILED" in captured.out
        assert "AWS access key ID" in captured.out

    def test_output_on_clean(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "fine.txt").write_text("all good", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["check_secrets.py", str(tmp_path)])

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "Secret scan passed" in captured.out
