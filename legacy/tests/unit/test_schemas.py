"""Shared JSON Schema contract tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from waccy.core.models import (
    CONTRACT_SCHEMA_VERSION,
    MappedFinancialDataset,
    NormalizedFinancialDataset,
    ThreeStatementModel,
    ValidatedFinancialDataset,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
GENERATOR_PATH = ROOT / "scripts" / "generate-schemas.py"

if TYPE_CHECKING:
    from types import ModuleType


def test_root_contract_models_have_schema_version_default() -> None:
    """Root polyglot contract models expose the current schema version."""
    for model in (
        NormalizedFinancialDataset,
        MappedFinancialDataset,
        ValidatedFinancialDataset,
        ThreeStatementModel,
    ):
        assert model.model_fields["schema_version"].default == CONTRACT_SCHEMA_VERSION


def test_committed_schema_artifacts_include_expected_contracts() -> None:
    """Schema artifacts are loadable and expose stable WACCY metadata."""
    expected = {
        "financial-dataset.schema.json": {
            "title": "FinancialDatasetContracts",
            "defs": {
                "NormalizedFinancialDataset",
                "MappedFinancialDataset",
                "ValidatedFinancialDataset",
            },
        },
        "model-output.schema.json": {
            "title": "ThreeStatementModel",
            "defs": {"FinancialStatement", "StatementLine", "ValidationIssue"},
        },
        "diagnostics.schema.json": {
            "title": "DiagnosticContracts",
            "defs": {"MappingDiagnostic", "ValidationIssue"},
        },
    }

    for filename, expectation in expected.items():
        schema = json.loads((SCHEMA_DIR / filename).read_text())

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == f"https://decisionnerd.github.io/waccy/schemas/{filename}"
        assert schema["x-waccy-schema-version"] == CONTRACT_SCHEMA_VERSION
        assert schema["x-waccy-generated-from"] == "waccy.core.models"
        assert schema["title"] == expectation["title"]
        assert expectation["defs"].issubset(schema.get("$defs", {}))


def test_contract_schema_version_is_required_and_const() -> None:
    """Generated schemas enforce payload-level schema_version compatibility."""
    financial_dataset = json.loads((SCHEMA_DIR / "financial-dataset.schema.json").read_text())
    model_output = json.loads((SCHEMA_DIR / "model-output.schema.json").read_text())
    diagnostics = json.loads((SCHEMA_DIR / "diagnostics.schema.json").read_text())

    for name in (
        "NormalizedFinancialDataset",
        "MappedFinancialDataset",
        "ValidatedFinancialDataset",
    ):
        definition = financial_dataset["$defs"][name]
        assert "schema_version" in definition["required"]
        assert definition["properties"]["schema_version"]["const"] == CONTRACT_SCHEMA_VERSION

    assert "schema_version" in model_output["required"]
    assert model_output["properties"]["schema_version"]["const"] == CONTRACT_SCHEMA_VERSION
    assert "schema_version" not in diagnostics.get("properties", {})


def test_schema_generator_matches_committed_artifacts() -> None:
    """Generated Pydantic schemas match the committed JSON artifacts."""
    generator = _load_schema_generator()

    assert generator.check_schemas() == []
    for filename, content in generator.render_schemas().items():
        assert (SCHEMA_DIR / filename).read_text() == content


def _load_schema_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("waccy_schema_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load schema generator.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
