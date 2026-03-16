"""Comprehensive tests for scripts/create_mcp.py."""

import argparse
import json
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Import helpers — monkeypatch REPO_ROOT before importing the module so that
# McpConfig.mcp_dir resolves under the tmp directory used in each test.
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
)


@pytest.fixture(autouse=True)
def _patch_repo_root(tmp_path, monkeypatch):
    """Point REPO_ROOT at tmp_path for every test so file I/O is sandboxed."""
    monkeypatch.syspath_prepend(SCRIPT_DIR)
    import create_mcp

    monkeypatch.setattr(create_mcp, "REPO_ROOT", str(tmp_path))


def _import():
    """Return the create_mcp module (already on sys.path via the fixture)."""
    import create_mcp

    return create_mcp


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_namespace(**overrides):
    """Build an argparse.Namespace with sensible defaults, overridden by kwargs."""
    defaults = dict(
        name="my_server",
        package="my-server-mcp",
        description="",
        category="utilities",
        auth="none",
        auth_env="",
        auth_provider="",
        tools=[],
        capabilities=[],
        author="",
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# ═══════════════════════════════════════════════════════════════════════════
# A. McpConfig dataclass
# ═══════════════════════════════════════════════════════════════════════════


class TestMcpConfig:
    def test_default_values(self):
        mod = _import()
        cfg = mod.McpConfig(name="foo", package="foo-mcp")
        assert cfg.description == ""
        assert cfg.category == "utilities"
        assert cfg.auth_type == "none"
        assert cfg.auth_env == ""
        assert cfg.auth_provider == ""
        assert cfg.tools == []
        assert cfg.capabilities == []
        assert cfg.author == ""

    def test_mcp_dir_property(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(name="bar", package="bar-mcp")
        expected = os.path.join(str(tmp_path), "mcps", "bar")
        assert cfg.mcp_dir == expected


# ═══════════════════════════════════════════════════════════════════════════
# B. validate_name
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateName:
    @pytest.mark.parametrize("name", ["a", "abc", "foo_bar", "x1", "a0_b1_c2"])
    def test_valid_names_pass(self, name):
        mod = _import()
        # Should NOT raise / exit
        mod.validate_name(name)

    @pytest.mark.parametrize(
        "name",
        [
            "Uppercase",
            "has-hyphens",
            "has spaces",
            "1starts_with_number",
            "_leading_underscore",
            "",
        ],
    )
    def test_invalid_names_exit(self, name):
        mod = _import()
        with pytest.raises(SystemExit) as exc_info:
            mod.validate_name(name)
        assert exc_info.value.code == 1


# ═══════════════════════════════════════════════════════════════════════════
# C. validate_auth
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateAuth:
    def test_none_passes(self):
        mod = _import()
        args = _make_namespace(auth="none")
        mod.validate_auth(args)  # should not exit

    def test_api_key_without_auth_env_exits(self):
        mod = _import()
        args = _make_namespace(auth="api_key", auth_env="")
        with pytest.raises(SystemExit) as exc_info:
            mod.validate_auth(args)
        assert exc_info.value.code == 1

    def test_api_key_with_auth_env_passes(self):
        mod = _import()
        args = _make_namespace(auth="api_key", auth_env="MY_KEY")
        mod.validate_auth(args)

    def test_oauth2_without_auth_provider_exits(self):
        mod = _import()
        args = _make_namespace(auth="oauth2", auth_provider="")
        with pytest.raises(SystemExit) as exc_info:
            mod.validate_auth(args)
        assert exc_info.value.code == 1

    def test_oauth2_with_auth_provider_passes(self):
        mod = _import()
        args = _make_namespace(auth="oauth2", auth_provider="google")
        mod.validate_auth(args)


# ═══════════════════════════════════════════════════════════════════════════
# D. create_meta
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateMeta:
    def test_writes_valid_json_with_all_fields(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="test_srv",
            package="test-srv-mcp",
            description="A test server",
            category="search",
            auth_type="none",
            tools=["search", "fetch"],
            capabilities=["web search"],
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_meta(cfg)

        meta_path = os.path.join(cfg.mcp_dir, "meta.json")
        with open(meta_path) as f:
            meta = json.load(f)

        assert meta["name"] == "test_srv"
        assert meta["version"] == "1.0.0"
        assert meta["description"] == "A test server"
        assert meta["source"] == "npm"
        assert meta["package"] == "test-srv-mcp"
        assert meta["command"] == ["npx", "-y", "test-srv-mcp"]
        assert meta["auth_type"] == "none"
        assert meta["tools"] == ["search", "fetch"]
        assert meta["capabilities"] == ["web search"]
        assert meta["category"] == "search"
        # auth_env and auth_provider should be absent when empty
        assert "auth_env" not in meta
        assert "auth_provider" not in meta

    def test_includes_auth_env_when_set(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="key_srv",
            package="key-mcp",
            auth_type="api_key",
            auth_env="MY_SECRET",
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_meta(cfg)

        with open(os.path.join(cfg.mcp_dir, "meta.json")) as f:
            meta = json.load(f)

        assert meta["auth_env"] == "MY_SECRET"
        assert "auth_provider" not in meta

    def test_includes_auth_provider_when_set(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="oauth_srv",
            package="oauth-mcp",
            auth_type="oauth2",
            auth_provider="github",
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_meta(cfg)

        with open(os.path.join(cfg.mcp_dir, "meta.json")) as f:
            meta = json.load(f)

        assert meta["auth_provider"] == "github"
        assert "auth_env" not in meta

    def test_includes_author_when_set(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="auth_srv",
            package="auth-mcp",
            author="octocat",
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_meta(cfg)

        with open(os.path.join(cfg.mcp_dir, "meta.json")) as f:
            meta = json.load(f)

        assert meta["author"] == {"github": "octocat"}


# ═══════════════════════════════════════════════════════════════════════════
# E. create_readme
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateReadme:
    def test_contains_package_name(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(name="demo", package="demo-mcp", description="Demo server")
        os.makedirs(cfg.mcp_dir)
        mod.create_readme(cfg)

        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "demo-mcp" in readme

    def test_auth_section_none(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(name="demo", package="demo-mcp", auth_type="none")
        os.makedirs(cfg.mcp_dir)
        mod.create_readme(cfg)

        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "No authentication required." in readme

    def test_auth_section_api_key(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="demo",
            package="demo-mcp",
            auth_type="api_key",
            auth_env="DEMO_KEY",
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_readme(cfg)

        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "DEMO_KEY" in readme
        assert "API key" in readme

    def test_auth_section_oauth2(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="demo",
            package="demo-mcp",
            auth_type="oauth2",
            auth_provider="google",
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_readme(cfg)

        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "OAuth2" in readme
        assert "google" in readme

    def test_tools_listed(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="demo", package="demo-mcp", tools=["search", "query"]
        )
        os.makedirs(cfg.mcp_dir)
        mod.create_readme(cfg)

        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "- `search`" in readme
        assert "- `query`" in readme

    def test_no_tools_placeholder(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(name="demo", package="demo-mcp", tools=[])
        os.makedirs(cfg.mcp_dir)
        mod.create_readme(cfg)

        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "Tools not yet enumerated" in readme


# ═══════════════════════════════════════════════════════════════════════════
# F. _build_auth_section
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildAuthSection:
    def test_none(self):
        mod = _import()
        cfg = mod.McpConfig(name="x", package="x-mcp", auth_type="none")
        assert mod._build_auth_section(cfg) == "No authentication required."

    def test_api_key(self):
        mod = _import()
        cfg = mod.McpConfig(
            name="x", package="x-mcp", auth_type="api_key", auth_env="X_KEY"
        )
        result = mod._build_auth_section(cfg)
        assert "API key" in result
        assert "`X_KEY`" in result

    def test_oauth2(self):
        mod = _import()
        cfg = mod.McpConfig(
            name="x",
            package="x-mcp",
            auth_type="oauth2",
            auth_provider="slack",
        )
        result = mod._build_auth_section(cfg)
        assert "OAuth2" in result
        assert "slack" in result


# ═══════════════════════════════════════════════════════════════════════════
# G. build_config
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildConfig:
    def test_name_normalization_hyphens(self):
        mod = _import()
        args = _make_namespace(name="my-cool-server")
        cfg = mod.build_config(args)
        assert cfg.name == "my_cool_server"

    def test_name_normalization_uppercase(self):
        mod = _import()
        args = _make_namespace(name="MyServer")
        cfg = mod.build_config(args)
        assert cfg.name == "myserver"

    def test_auto_description_when_empty(self):
        mod = _import()
        args = _make_namespace(name="brave_search", package="brave-search-mcp")
        cfg = mod.build_config(args)
        assert "Brave Search" in cfg.description
        assert "brave-search-mcp" in cfg.description

    def test_explicit_description_preserved(self):
        mod = _import()
        args = _make_namespace(description="Custom desc")
        cfg = mod.build_config(args)
        assert cfg.description == "Custom desc"

    def test_auto_capabilities_when_empty(self):
        mod = _import()
        args = _make_namespace(name="brave_search", capabilities=[])
        cfg = mod.build_config(args)
        assert cfg.capabilities == ["brave search"]

    def test_explicit_capabilities_preserved(self):
        mod = _import()
        args = _make_namespace(capabilities=["web", "search"])
        cfg = mod.build_config(args)
        assert cfg.capabilities == ["web", "search"]

    def test_invalid_name_after_normalization_exits(self):
        mod = _import()
        args = _make_namespace(name="123bad")
        with pytest.raises(SystemExit):
            mod.build_config(args)


# ═══════════════════════════════════════════════════════════════════════════
# H. scaffold_mcp
# ═══════════════════════════════════════════════════════════════════════════


class TestScaffoldMcp:
    def test_creates_directory_and_files(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(
            name="new_srv",
            package="new-srv-mcp",
            description="Brand new",
            tools=["do_thing"],
        )
        mod.scaffold_mcp(cfg)

        assert os.path.isdir(cfg.mcp_dir)
        assert os.path.isfile(os.path.join(cfg.mcp_dir, "meta.json"))
        assert os.path.isfile(os.path.join(cfg.mcp_dir, "README.md"))

        # meta.json is valid and contains expected data
        with open(os.path.join(cfg.mcp_dir, "meta.json")) as f:
            meta = json.load(f)
        assert meta["name"] == "new_srv"
        assert meta["tools"] == ["do_thing"]

        # README mentions the package
        readme = open(os.path.join(cfg.mcp_dir, "README.md")).read()
        assert "new-srv-mcp" in readme

    def test_existing_directory_exits(self, tmp_path):
        mod = _import()
        cfg = mod.McpConfig(name="existing", package="existing-mcp")
        os.makedirs(cfg.mcp_dir)

        with pytest.raises(SystemExit) as exc_info:
            mod.scaffold_mcp(cfg)
        assert exc_info.value.code == 1
