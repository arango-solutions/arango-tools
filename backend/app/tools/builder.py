"""Pure argv construction from a tool spec, user params, and a connection."""

from __future__ import annotations

import shlex

from app.connection import ConnectionState, to_tools_endpoint

from .registry import FieldSpec, ToolSpec

PASSWORD_MASK = "********"


def _is_empty(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _split_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value]
    else:
        items = str(value).split(",")
    return [item.strip() for item in items if item.strip()]


def _render_field(field: FieldSpec, value: object) -> list[str]:
    """Render a single field into argv tokens (empty list when omitted)."""
    if field.type == "bool":
        if value is True:
            return [field.flag, "true"]
        # Only emit an explicit "false" when overriding a default-on flag.
        if value is False and field.default is True:
            return [field.flag, "false"]
        return []

    if _is_empty(value):
        return []

    if field.type == "list":
        items = _split_list(value)
        if not items:
            return []
        if field.repeatable:
            tokens: list[str] = []
            for item in items:
                tokens.extend([field.flag, item])
            return tokens
        return [field.flag, ",".join(items)]

    if field.positional:
        return [str(value)]

    return [field.flag, str(value)]


def validate_params(tool: ToolSpec, params: dict) -> list[str]:
    """Return a list of human-readable validation errors (empty when valid)."""
    errors: list[str] = []
    for field in tool.fields:
        if field.required:
            value = params.get(field.key)
            if field.type == "bool":
                continue
            if _is_empty(value) or (field.type == "list" and not _split_list(value)):
                errors.append(f"'{field.label}' is required.")
    return errors


def _connection_args(connection: ConnectionState, *, mask_password: bool) -> list[str]:
    password = PASSWORD_MASK if mask_password else (connection.password or "")
    return [
        "--server.endpoint", to_tools_endpoint(connection.endpoint),
        "--server.database", connection.database or "_system",
        "--server.username", connection.username or "root",
        "--server.password", password,
        "--server.authentication", "true",
    ]


def build_argv(
    tool: ToolSpec,
    params: dict,
    connection: ConnectionState | None = None,
    *,
    binary: str | None = None,
    mask_password: bool = False,
) -> list[str]:
    """Build the full argv (argv[0] = binary) for a tool invocation.

    Connection flags are prepended for tools with ``connects=True``. Flags are
    emitted before positional arguments. The free-text ``extra_args`` field is
    shell-split and appended last.
    """
    argv: list[str] = [binary or tool.binary]

    if tool.connects and connection is not None:
        argv.extend(_connection_args(connection, mask_password=mask_password))

    positionals: list[str] = []
    for field in tool.fields:
        if field.key == "extra_args":
            continue
        tokens = _render_field(field, params.get(field.key))
        if field.positional:
            positionals.extend(tokens)
        else:
            argv.extend(tokens)

    argv.extend(positionals)

    extra = params.get("extra_args")
    if isinstance(extra, str) and extra.strip():
        argv.extend(shlex.split(extra))

    return argv
