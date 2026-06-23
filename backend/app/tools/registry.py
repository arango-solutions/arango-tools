"""Declarative specifications for the ArangoDB client tools.

Each :class:`ToolSpec` drives both the JSON schema sent to the frontend and the
argv construction in :mod:`app.tools.builder`. Only the commonly used options are
modelled explicitly; an ``extra_args`` free-text field on every tool acts as an
escape hatch for anything not covered here.

Foxx CLI is intentionally excluded: Foxx (and ``foxx-cli``) were removed in
ArangoDB 4.0.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

FieldType = Literal["string", "int", "bool", "enum", "path", "list", "text"]

DOC_BASE = "https://docs.arango.ai/arangodb/stable/components/tools"


class FieldSpec(BaseModel):
    key: str
    flag: str = ""  # CLI flag, e.g. "--collection". Empty for positional args.
    type: FieldType = "string"
    label: str
    help: str = ""
    default: object | None = None
    required: bool = False
    positional: bool = False
    repeatable: bool = False  # for "list": emit the flag once per value
    options: list[str] = []  # for "enum"
    placeholder: str = ""
    group: Literal["Common", "Advanced"] = "Common"


class ToolSpec(BaseModel):
    name: str
    binary: str
    title: str
    description: str
    connects: bool = True
    fields: list[FieldSpec] = []
    doc_url: str = ""


_EXTRA_ARGS = FieldSpec(
    key="extra_args",
    flag="",
    type="text",
    label="Advanced raw flags",
    help="Additional command-line flags passed verbatim (parsed like a shell line).",
    placeholder="--threads 4 --log.level info",
    group="Advanced",
)


def _tool(spec: ToolSpec) -> ToolSpec:
    """Append the shared extra-args field and a doc URL to a tool spec."""
    spec.fields = [*spec.fields, _EXTRA_ARGS.model_copy()]
    if not spec.doc_url:
        spec.doc_url = f"{DOC_BASE}/{spec.binary}/"
    return spec


TOOLS: dict[str, ToolSpec] = {}


def _register(spec: ToolSpec) -> None:
    TOOLS[spec.name] = _tool(spec)


_register(
    ToolSpec(
        name="arangodump",
        binary="arangodump",
        title="Dump",
        description="Create a backup of databases and collections to a local directory.",
        fields=[
            FieldSpec(key="output_directory", flag="--output-directory", type="path",
                      label="Output directory", required=True, placeholder="dump",
                      help="Directory the dump is written to."),
            FieldSpec(key="collection", flag="--collection", type="list", repeatable=True,
                      label="Collections", placeholder="users, orders",
                      help="Restrict the dump to these collections (comma-separated)."),
            FieldSpec(key="all_databases", flag="--all-databases", type="bool", default=False,
                      label="All databases", help="Dump all databases (requires root)."),
            FieldSpec(key="include_system_collections", flag="--include-system-collections",
                      type="bool", default=False, label="Include system collections"),
            FieldSpec(key="dump_data", flag="--dump-data", type="bool", default=True,
                      label="Dump document data", help="Disable to dump structure only."),
            FieldSpec(key="overwrite", flag="--overwrite", type="bool", default=False,
                      label="Overwrite existing output"),
            FieldSpec(key="compress_output", flag="--compress-output", type="bool", default=True,
                      label="Compress output"),
            FieldSpec(key="threads", flag="--threads", type="int", label="Threads",
                      placeholder="2", group="Advanced"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangorestore",
        binary="arangorestore",
        title="Restore",
        description="Load a dump created by arangodump back into an instance.",
        fields=[
            FieldSpec(key="input_directory", flag="--input-directory", type="path", required=True,
                      label="Input directory", placeholder="dump",
                      help="Directory containing the dump to restore."),
            FieldSpec(key="collection", flag="--collection", type="list", repeatable=True,
                      label="Collections", placeholder="users, orders",
                      help="Restrict the restore to these collections."),
            FieldSpec(key="create_collection", flag="--create-collection", type="bool", default=True,
                      label="Create collections"),
            FieldSpec(key="import_data", flag="--import-data", type="bool", default=True,
                      label="Import document data"),
            FieldSpec(key="overwrite", flag="--overwrite", type="bool", default=True,
                      label="Overwrite existing collections"),
            FieldSpec(key="all_databases", flag="--all-databases", type="bool", default=False,
                      label="All databases"),
            FieldSpec(key="include_system_collections", flag="--include-system-collections",
                      type="bool", default=False, label="Include system collections"),
            FieldSpec(key="threads", flag="--threads", type="int", label="Threads",
                      placeholder="2", group="Advanced"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangobackup",
        binary="arangobackup",
        title="Backup",
        description="Perform consistent hot backup operations on an instance.",
        fields=[
            FieldSpec(key="operation", type="enum", positional=True, required=True,
                      label="Operation", default="list",
                      options=["create", "list", "delete", "restore", "upload", "download"],
                      help="Hot backup operation to perform."),
            FieldSpec(key="label", flag="--label", type="string", label="Label",
                      help="Human-readable label for a created backup."),
            FieldSpec(key="identifier", flag="--identifier", type="string", label="Identifier",
                      help="Backup id (required for delete/restore/upload/download)."),
            FieldSpec(key="allow_inconsistent", flag="--allow-inconsistent", type="bool",
                      default=False, label="Allow inconsistent",
                      help="Proceed even if a consistent snapshot cannot be taken in time."),
            FieldSpec(key="max_wait_for_lock", flag="--max-wait-for-lock", type="int",
                      label="Max wait for lock (s)", group="Advanced"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangoimport",
        binary="arangoimport",
        title="Import",
        description="Bulk-import JSON, JSONL, CSV, or TSV data into a collection.",
        fields=[
            FieldSpec(key="file", flag="--file", type="path", required=True, label="Input file",
                      placeholder="data.json", help="Source file to import."),
            FieldSpec(key="collection", flag="--collection", type="string", required=True,
                      label="Target collection"),
            FieldSpec(key="type", flag="--type", type="enum", default="json",
                      options=["auto", "json", "jsonl", "csv", "tsv"], label="File type"),
            FieldSpec(key="create_collection", flag="--create-collection", type="bool",
                      default=False, label="Create collection if missing"),
            FieldSpec(key="create_collection_type", flag="--create-collection-type", type="enum",
                      default="document", options=["document", "edge"],
                      label="New collection type"),
            FieldSpec(key="overwrite", flag="--overwrite", type="bool", default=False,
                      label="Overwrite collection contents"),
            FieldSpec(key="on_duplicate", flag="--on-duplicate", type="enum", default="error",
                      options=["error", "update", "replace", "ignore"], label="On duplicate key"),
            FieldSpec(key="separator", flag="--separator", type="string", label="Separator (CSV/TSV)",
                      placeholder=",", group="Advanced"),
            FieldSpec(key="headers_file", flag="--headers-file", type="path",
                      label="Headers file (CSV/TSV)", group="Advanced"),
            FieldSpec(key="threads", flag="--threads", type="int", label="Threads",
                      placeholder="2", group="Advanced"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangoexport",
        binary="arangoexport",
        title="Export",
        description="Bulk-export collections or AQL query results to JSON, JSONL, CSV, or XML.",
        fields=[
            FieldSpec(key="type", flag="--type", type="enum", default="json",
                      options=["json", "jsonl", "csv", "xml"], label="Output type"),
            FieldSpec(key="output_directory", flag="--output-directory", type="path",
                      label="Output directory", placeholder="export"),
            FieldSpec(key="collection", flag="--collection", type="list", repeatable=True,
                      label="Collections", placeholder="users, orders",
                      help="Collections to export (mutually exclusive with a query)."),
            FieldSpec(key="query", flag="--query", type="text", label="AQL query",
                      help="Export the result of this AQL query instead of collections.",
                      placeholder="FOR u IN users RETURN u"),
            FieldSpec(key="fields", flag="--fields", type="string", label="Fields (CSV/XML)",
                      placeholder="_key,name,email", group="Advanced"),
            FieldSpec(key="overwrite", flag="--overwrite", type="bool", default=False,
                      label="Overwrite existing output"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangobench",
        binary="arangobench",
        title="Bench",
        description="Run performance benchmarks and functional tests against an instance.",
        fields=[
            FieldSpec(key="test_case", flag="--test-case", type="string", default="version",
                      label="Test case", placeholder="version",
                      help="Benchmark test case, e.g. version, document, aqlinsert."),
            FieldSpec(key="requests", flag="--requests", type="int", default=1000,
                      label="Total requests"),
            FieldSpec(key="concurrency", flag="--concurrency", type="int", default=1,
                      label="Concurrency"),
            FieldSpec(key="collection", flag="--collection", type="string", label="Collection",
                      placeholder="testcoll", group="Advanced"),
            FieldSpec(key="number_of_shards", flag="--number-of-shards", type="int",
                      label="Number of shards", group="Advanced"),
            FieldSpec(key="replication_factor", flag="--replication-factor", type="int",
                      label="Replication factor", group="Advanced"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangoinspect",
        binary="arangoinspect",
        title="Inspect",
        description="Gather server setup information to facilitate troubleshooting.",
        fields=[
            FieldSpec(key="output_directory", flag="--output-directory", type="path",
                      label="Output directory", placeholder="inspect", group="Advanced",
                      help="Directory the inspection report is written to."),
        ],
    )
)

_register(
    ToolSpec(
        name="arangosh",
        binary="arangosh",
        title="Shell",
        description="Run JavaScript against the server non-interactively (one-shot console).",
        fields=[
            FieldSpec(key="script", flag="--javascript.execute-string", type="text", required=True,
                      label="JavaScript to execute",
                      placeholder="db._query('RETURN 1').toArray()",
                      help="Executed via --javascript.execute-string."),
            FieldSpec(key="quiet", flag="--quiet", type="bool", default=True, label="Quiet startup",
                      group="Advanced"),
        ],
    )
)

_register(
    ToolSpec(
        name="arangovpack",
        binary="arangovpack",
        title="VPack",
        description="Validate and convert between VelocyPack and JSON (operates on local files).",
        connects=False,
        fields=[
            FieldSpec(key="input_type", flag="--input-type", type="enum", default="json",
                      options=["json", "vpack"], label="Input type"),
            FieldSpec(key="output_type", flag="--output-type", type="enum", default="json",
                      options=["json", "vpack"], label="Output type"),
            FieldSpec(key="pretty", flag="--pretty", type="bool", default=True,
                      label="Pretty-print output"),
            FieldSpec(key="print_non_json", flag="--print-non-json", type="bool", default=False,
                      label="Print non-JSON types", group="Advanced"),
            FieldSpec(key="input_file", type="path", positional=True, label="Input file",
                      help="Input file (reads stdin if omitted)."),
            FieldSpec(key="output_file", type="path", positional=True, label="Output file",
                      help="Output file (writes stdout if omitted)."),
        ],
    )
)

_register(
    ToolSpec(
        name="arangodb",
        binary="arangodb",
        title="Starter",
        description="Deploy and manage ArangoDB instances (ArangoDB Starter).",
        connects=False,
        fields=[
            FieldSpec(key="mode", flag="--starter.mode", type="enum", default="single",
                      options=["single", "cluster", "activefailover"], label="Deployment mode"),
            FieldSpec(key="data_dir", flag="--starter.data-dir", type="path", label="Data directory",
                      placeholder="./data"),
            FieldSpec(key="local", flag="--starter.local", type="bool", default=False,
                      label="Local cluster (single machine)"),
            FieldSpec(key="storage_engine", flag="--server.storage-engine", type="enum",
                      default="rocksdb", options=["rocksdb"], label="Storage engine",
                      group="Advanced"),
        ],
    )
)


def list_tools() -> list[ToolSpec]:
    return list(TOOLS.values())


def get_tool(name: str) -> ToolSpec | None:
    return TOOLS.get(name)
