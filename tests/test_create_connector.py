"""Comprehensive tests for scripts/create_connector.py scaffold utility."""

import argparse
import json
import os
import sys

import pytest

# Ensure the scripts package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.create_connector import (
    LANG_ALIASES,
    SUPPORTED_LANGUAGES,
    _build_node_package_json,
    _file_ext,
    _normalize_inputs,
    _scaffold_connector,
    create_config_template,
    create_gitignore,
    create_js_connector,
    create_meta,
    create_py_connector,
    create_readme,
    create_ts_connector,
)


# ---------------------------------------------------------------------------
# A. Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_lang_aliases_maps_js(self):
        assert LANG_ALIASES["js"] == "javascript"

    def test_lang_aliases_maps_ts(self):
        assert LANG_ALIASES["ts"] == "typescript"

    def test_lang_aliases_maps_py(self):
        assert LANG_ALIASES["py"] == "python"

    def test_supported_languages_contains_all(self):
        expected = {"javascript", "typescript", "python", "js", "ts", "py"}
        assert set(SUPPORTED_LANGUAGES) == expected


# ---------------------------------------------------------------------------
# B. _file_ext
# ---------------------------------------------------------------------------

class TestFileExt:
    @pytest.mark.parametrize("lang,ext", [
        ("javascript", "js"),
        ("typescript", "ts"),
        ("python", "py"),
    ])
    def test_returns_correct_extension(self, lang, ext):
        assert _file_ext(lang) == ext

    def test_unknown_language_raises(self):
        with pytest.raises(KeyError):
            _file_ext("ruby")


# ---------------------------------------------------------------------------
# C. _normalize_inputs
# ---------------------------------------------------------------------------

class TestNormalizeInputs:
    @staticmethod
    def _make_args(name, language, platform=None, author=""):
        return argparse.Namespace(name=name, language=language, platform=platform, author=author)

    def test_name_lowercased(self):
        name, _, _, _ = _normalize_inputs(self._make_args("MyBot", "javascript"))
        assert name == "mybot"

    def test_hyphens_to_underscores(self):
        name, _, _, _ = _normalize_inputs(self._make_args("my-bot", "javascript"))
        assert name == "my_bot"

    def test_spaces_to_underscores(self):
        name, _, _, _ = _normalize_inputs(self._make_args("my bot", "javascript"))
        assert name == "my_bot"

    def test_platform_defaults_to_name(self):
        _, platform, _, _ = _normalize_inputs(self._make_args("discord", "javascript"))
        assert platform == "discord"

    def test_platform_explicit(self):
        _, platform, _, _ = _normalize_inputs(self._make_args("mybot", "javascript", platform="slack"))
        assert platform == "slack"

    def test_language_alias_resolved_js(self):
        _, _, language, _ = _normalize_inputs(self._make_args("bot", "js"))
        assert language == "javascript"

    def test_language_alias_resolved_ts(self):
        _, _, language, _ = _normalize_inputs(self._make_args("bot", "ts"))
        assert language == "typescript"

    def test_language_alias_resolved_py(self):
        _, _, language, _ = _normalize_inputs(self._make_args("bot", "py"))
        assert language == "python"

    def test_full_language_name_unchanged(self):
        _, _, language, _ = _normalize_inputs(self._make_args("bot", "python"))
        assert language == "python"


# ---------------------------------------------------------------------------
# D. create_meta
# ---------------------------------------------------------------------------

class TestCreateMeta:
    def test_writes_valid_json_with_redis_channels(self, tmp_path):
        create_meta(str(tmp_path), "discord", "javascript", "discord", "testuser")
        meta_path = tmp_path / "meta.json"
        assert meta_path.exists()

        data = json.loads(meta_path.read_text())
        assert data["name"] == "discord"
        assert data["language"] == "javascript"
        assert data["platforms"] == ["discord"]
        assert data["author"] == {"github": "testuser"}
        assert "redis_channels" in data

        channels = data["redis_channels"]
        assert "brain:response" in channels["subscribe"]
        assert "brain:audio" in channels["subscribe"]
        assert "brain:task" in channels["publish"]
        assert "discord:monitor" in channels["publish"]

    def test_description_contains_platform(self, tmp_path):
        create_meta(str(tmp_path), "slack", "typescript", "slack", "")
        data = json.loads((tmp_path / "meta.json").read_text())
        assert "Slack" in data["description"]


# ---------------------------------------------------------------------------
# E. create_config_template
# ---------------------------------------------------------------------------

class TestCreateConfigTemplate:
    def test_writes_json_with_default_fields(self, tmp_path):
        create_config_template(str(tmp_path))
        path = tmp_path / "config-template.json"
        assert path.exists()

        data = json.loads(path.read_text())
        assert data["bot_name"] == "Sentient"
        assert data["bot_aliases"] == []
        assert data["whitelisted_users"] == []
        assert data["whitelisted_groups"] == []
        assert data["monitor_groups"] == []
        assert "_instructions" in data


# ---------------------------------------------------------------------------
# F. create_gitignore
# ---------------------------------------------------------------------------

class TestCreateGitignore:
    def test_contains_expected_entries(self, tmp_path):
        create_gitignore(str(tmp_path))
        content = (tmp_path / ".gitignore").read_text()
        assert "config.json" in content
        assert "node_modules/" in content
        assert "package-lock.json" in content


# ---------------------------------------------------------------------------
# G. create_readme
# ---------------------------------------------------------------------------

class TestCreateReadme:
    def test_contains_platform_name(self, tmp_path):
        create_readme(str(tmp_path), "discord", "discord", "javascript")
        content = (tmp_path / "README.md").read_text()
        assert "Discord" in content

    @pytest.mark.parametrize("language,expected_snippet", [
        ("javascript", "node connector.js"),
        ("typescript", "npx tsx connector.ts"),
        ("python", "pip install -r requirements.txt"),
    ])
    def test_language_specific_setup(self, tmp_path, language, expected_snippet):
        d = tmp_path / language
        d.mkdir()
        create_readme(str(d), "bot", "myplat", language)
        content = (d / "README.md").read_text()
        assert expected_snippet in content


# ---------------------------------------------------------------------------
# H. create_js_connector
# ---------------------------------------------------------------------------

class TestCreateJsConnector:
    def test_creates_package_json_and_connector_js(self, tmp_path):
        create_js_connector(str(tmp_path), "discord", "discord")

        pkg_path = tmp_path / "package.json"
        assert pkg_path.exists()
        pkg = json.loads(pkg_path.read_text())
        assert pkg["name"] == "sentient-discord"
        assert pkg["scripts"]["start"] == "node connector.js"
        assert "redis" in pkg["dependencies"]

        js_path = tmp_path / "connector.js"
        assert js_path.exists()
        content = js_path.read_text()
        assert 'ConnectorBase' in content
        assert 'new ConnectorBase("discord"' in content
        assert "sendText" in content


# ---------------------------------------------------------------------------
# I. create_ts_connector
# ---------------------------------------------------------------------------

class TestCreateTsConnector:
    def test_creates_package_json_and_connector_ts(self, tmp_path):
        create_ts_connector(str(tmp_path), "slack", "slack")

        pkg_path = tmp_path / "package.json"
        assert pkg_path.exists()
        pkg = json.loads(pkg_path.read_text())
        assert pkg["name"] == "sentient-slack"
        assert pkg["scripts"]["start"] == "npx tsx connector.ts"
        assert "tsx" in pkg["devDependencies"]
        assert "typescript" in pkg["devDependencies"]

        ts_path = tmp_path / "connector.ts"
        assert ts_path.exists()
        content = ts_path.read_text()
        assert 'ConnectorBase' in content
        assert 'new ConnectorBase("slack"' in content
        assert "chatId: string" in content


# ---------------------------------------------------------------------------
# J. create_py_connector
# ---------------------------------------------------------------------------

class TestCreatePyConnector:
    def test_creates_connector_py_and_requirements(self, tmp_path):
        create_py_connector(str(tmp_path), "telegram", "telegram")

        py_path = tmp_path / "connector.py"
        assert py_path.exists()
        content = py_path.read_text()
        assert "Telegram" in content
        assert "redis" in content.lower()
        assert "brain:response" in content

        req_path = tmp_path / "requirements.txt"
        assert req_path.exists()
        assert "redis" in req_path.read_text()


# ---------------------------------------------------------------------------
# K. _build_node_package_json
# ---------------------------------------------------------------------------

class TestBuildNodePackageJson:
    def test_js_no_dev_dependencies(self):
        pkg = _build_node_package_json("mybot", "javascript")
        assert "devDependencies" not in pkg
        assert pkg["scripts"]["start"] == "node connector.js"
        assert "redis" in pkg["dependencies"]

    def test_ts_has_tsx_and_typescript(self):
        pkg = _build_node_package_json("mybot", "typescript")
        assert "devDependencies" in pkg
        assert "tsx" in pkg["devDependencies"]
        assert "typescript" in pkg["devDependencies"]
        assert pkg["scripts"]["start"] == "npx tsx connector.ts"


# ---------------------------------------------------------------------------
# L. _scaffold_connector integration
# ---------------------------------------------------------------------------

class TestScaffoldConnectorIntegration:
    @staticmethod
    def _expected_common_files():
        return {"meta.json", "config-template.json", ".gitignore", "README.md"}

    def test_js_creates_6_files(self, tmp_path, monkeypatch):
        import scripts.create_connector as mod
        monkeypatch.setattr(mod, "REPO_ROOT", str(tmp_path))

        connector_dir = str(tmp_path / "connectors" / "discord")
        _scaffold_connector(connector_dir, "discord", "discord", "javascript", "author")

        files = set(os.listdir(connector_dir))
        expected = self._expected_common_files() | {"package.json", "connector.js"}
        assert files == expected
        assert len(files) == 6

    def test_ts_creates_6_files(self, tmp_path, monkeypatch):
        import scripts.create_connector as mod
        monkeypatch.setattr(mod, "REPO_ROOT", str(tmp_path))

        connector_dir = str(tmp_path / "connectors" / "slack")
        _scaffold_connector(connector_dir, "slack", "slack", "typescript", "author")

        files = set(os.listdir(connector_dir))
        expected = self._expected_common_files() | {"package.json", "connector.ts"}
        assert files == expected
        assert len(files) == 6

    def test_python_creates_6_files(self, tmp_path, monkeypatch):
        import scripts.create_connector as mod
        monkeypatch.setattr(mod, "REPO_ROOT", str(tmp_path))

        connector_dir = str(tmp_path / "connectors" / "telegram")
        _scaffold_connector(connector_dir, "telegram", "telegram", "python", "author")

        files = set(os.listdir(connector_dir))
        expected = self._expected_common_files() | {"connector.py", "requirements.txt"}
        assert files == expected
        assert len(files) == 6


# ---------------------------------------------------------------------------
# M. Existing directory exits with error
# ---------------------------------------------------------------------------

class TestExistingDirectoryExits:
    def test_main_exits_when_directory_exists(self, tmp_path, monkeypatch):
        import scripts.create_connector as mod
        monkeypatch.setattr(mod, "REPO_ROOT", str(tmp_path))

        # Pre-create the connector directory
        connector_dir = tmp_path / "connectors" / "discord"
        connector_dir.mkdir(parents=True)

        # Simulate CLI args
        monkeypatch.setattr(
            "sys.argv",
            ["create_connector.py", "discord", "--language", "javascript"],
        )

        with pytest.raises(SystemExit) as exc_info:
            mod.main()

        assert exc_info.value.code == 1
