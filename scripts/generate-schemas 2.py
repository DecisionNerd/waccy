"""Generate WACCY JSON Schema artifacts from the Python contract models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from waccy.core.models import (
    CONTRACT_SCHEMA_VERSION,
    MappedFinancialDataset,
    MappingDiagnostic,
    NormalizedFinancialDataset,
    ThreeStatementModel,
    ValidatedFinancialDataset,
    ValidationIssue,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


class FinancialDatasetContracts(BaseModel):
    """Grouped schema roots for dataset contract consumers."""

    normalized_financial_dataset: NormalizedFinancialDataset
    mapped_financial_dataset: MappedFinancialDataset
    validated_financial_dataset: ValidatedFinancialDataset


class DiagnosticContracts(BaseModel):
    """Grouped schema roots for mapping and validation diagnostics."""

    mapping_diagnostic: MappingDiagnostic
    validation_issue: ValidationIssue


SCHEMAS: dict[str, type[BaseModel]] = {
    "financial-dataset.schema.json": FinancialDatasetContracts,
    "model-output.schema.json": ThreeStatementModel,
    "diagnostics.schema.json": DiagnosticContracts,
}


def _schema_for(model: type[BaseModel], filename: str) -> dict[str, Any]:
    schema = model.model_json_schema()
    _enforce_schema_version_contract(schema)
    schema["$id"] = f"https://decisionnerd.github.io/waccy/schemas/{filename}"
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["x-waccy-schema-version"] = CONTRACT_SCHEMA_VERSION
    schema["x-waccy-generated-from"] = "waccy.core.models"
    return schema


def _enforce_schema_version_contract(schema: dict[str, Any]) -> None:
    """Require schema_version consts on generated contract objects that define it."""
    properties = schema.get("properties")
    if isinstance(properties, dict) and "schema_version" in properties:
        schema_version = properties["schema_version"]
        if isinstance(schema_version, dict):
            schema_version["const"] = CONTRACT_SCHEMA_VERSION
            schema_version["default"] = CONTRACT_SCHEMA_VERSION
        required = schema.setdefault("required", [])
        if isinstance(required, list) and "schema_version" not in required:
            required.append("schema_version")
            required.sort()

    for value in schema.values():
        if isinstance(value, dict):
            _enforce_schema_version_contract(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _enforce_schema_version_contract(item)


def render_schemas() -> dict[str, str]:
    """Return deterministic schema file contents keyed by filename."""
    return {
        filename: json.dumps(_schema_for(model, filename), indent=2, sort_keys=True) + "\n"
        for filename, model in SCHEMAS.items()
    }


def write_schemas() -> None:
    """Write generated schemas to the repository schema directory."""
    SCHEMA_DIR.mkdir(exist_ok=True)
    for filename, content in render_schemas().items():
        (SCHEMA_DIR / filename).write_text(content)


def check_schemas() -> list[str]:
    """Return names of schema artifacts that differ from generated output."""
    mismatches = []
    for filename, content in render_schemas().items():
        path = SCHEMA_DIR / filename
        if not path.exists() or path.read_text() != content:
            mismatches.append(filename)
    return mismatches


def main() -> int:
    """Run the schema generator or drift check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed schema artifacts differ from generated output",
    )
    args = parser.parse_args()

    if args.check:
        mismatches = check_schemas()
        if mismatches:
            joined = ", ".join(mismatches)
            print(f"Schema artifacts are out of date: {joined}")
            return 1
        print("Schema artifacts are current.")
        return 0

    write_schemas()
    print(f"Wrote {len(SCHEMAS)} schema artifacts to {SCHEMA_DIR.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
