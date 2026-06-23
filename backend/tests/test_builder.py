"""Tests for pure argv construction and validation."""

from __future__ import annotations

from app.connection import ConnectionState
from app.tools.builder import PASSWORD_MASK, build_argv, validate_params
from app.tools.registry import get_tool


def _conn() -> ConnectionState:
    return ConnectionState(
        endpoint="http://db.example.com:8529",
        database="mydb",
        username="root",
        password="s3cret",
        source="manual",
    )


def test_build_argv_connecting_tool_prepends_connection_flags():
    tool = get_tool("arangodump")
    argv = build_argv(tool, {"output_directory": "dump"}, _conn())

    assert argv[0] == "arangodump"
    assert "--server.endpoint" in argv
    # http:// is converted to the tools' tcp:// scheme.
    idx = argv.index("--server.endpoint")
    assert argv[idx + 1] == "tcp://db.example.com:8529"
    assert "--server.database" in argv and argv[argv.index("--server.database") + 1] == "mydb"
    assert "--server.password" in argv and argv[argv.index("--server.password") + 1] == "s3cret"
    assert "--output-directory" in argv and argv[argv.index("--output-directory") + 1] == "dump"


def test_build_argv_non_connecting_tool_has_no_connection_flags():
    tool = get_tool("arangovpack")
    argv = build_argv(tool, {"input_type": "json", "output_type": "vpack"}, _conn())

    assert "--server.endpoint" not in argv
    assert "--server.password" not in argv
    assert "--input-type" in argv
    assert "--output-type" in argv


def test_build_argv_masks_password_when_requested():
    tool = get_tool("arangodump")
    argv = build_argv(tool, {"output_directory": "dump"}, _conn(), mask_password=True)
    assert PASSWORD_MASK in argv
    assert "s3cret" not in argv


def test_build_argv_https_endpoint_converts_to_ssl():
    tool = get_tool("arangodump")
    conn = ConnectionState(endpoint="https://secure:8530", database="_system", source="manual")
    argv = build_argv(tool, {"output_directory": "dump"}, conn)
    assert "ssl://secure:8530" in argv


def test_bool_default_true_emits_false_when_disabled():
    tool = get_tool("arangodump")
    # compress_output defaults to True; turning it off should emit "false".
    argv = build_argv(tool, {"output_directory": "dump", "compress_output": False}, _conn())
    idx = argv.index("--compress-output")
    assert argv[idx + 1] == "false"


def test_bool_default_false_omitted_when_disabled():
    tool = get_tool("arangodump")
    argv = build_argv(tool, {"output_directory": "dump", "overwrite": False}, _conn())
    assert "--overwrite" not in argv


def test_list_field_is_repeatable():
    tool = get_tool("arangodump")
    argv = build_argv(tool, {"output_directory": "dump", "collection": "users, orders"}, _conn())
    occurrences = [argv[i + 1] for i, a in enumerate(argv) if a == "--collection"]
    assert occurrences == ["users", "orders"]


def test_positional_argument_appended_without_flag():
    tool = get_tool("arangobackup")
    argv = build_argv(tool, {"operation": "create", "label": "nightly"}, _conn())
    assert "create" in argv
    assert "--operation" not in argv
    assert "--label" in argv and argv[argv.index("--label") + 1] == "nightly"


def test_extra_args_are_shell_split_and_appended():
    tool = get_tool("arangodump")
    argv = build_argv(
        tool, {"output_directory": "dump", "extra_args": "--threads 4 --log.level info"}, _conn()
    )
    assert argv[-4:] == ["--threads", "4", "--log.level", "info"]


def test_validate_params_reports_missing_required_field():
    tool = get_tool("arangoimport")
    errors = validate_params(tool, {"collection": "users"})  # missing required --file
    assert any("Input file" in e for e in errors)


def test_validate_params_passes_when_required_present():
    tool = get_tool("arangoimport")
    errors = validate_params(tool, {"file": "data.json", "collection": "users"})
    assert errors == []
