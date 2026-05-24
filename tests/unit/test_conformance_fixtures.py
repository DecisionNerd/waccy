"""Cross-language conformance fixture tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from waccy.core.models import (
    CONTRACT_SCHEMA_VERSION,
    MappedFinancialDataset,
    NormalizedFinancialDataset,
    ThreeStatementModel,
    ValidatedFinancialDataset,
    ValidationIssue,
)

ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE_DIR = ROOT / "tests" / "conformance"
GENERATOR_PATH = ROOT / "scripts" / "generate-conformance-fixtures.py"
SOURCES = ("qbo", "edgar")

if TYPE_CHECKING:
    from types import ModuleType


def test_conformance_fixture_files_exist_for_qbo_and_edgar() -> None:
    """Each source case exposes every committed conformance artifact."""
    expected_files = {
        "source-fixture.json",
        "expected-normalized.json",
        "expected-mapped.json",
        "expected-validated.json",
        "expected-model.json",
        "expected-diagnostics.json",
    }

    for source in SOURCES:
        actual_files = {path.name for path in (CONFORMANCE_DIR / source).iterdir()}

        assert actual_files == expected_files


def test_conformance_contract_artifacts_validate_with_pydantic_models() -> None:
    """Committed golden outputs load through the Python reference contracts."""
    for source in SOURCES:
        source_fixture = _load_json(source, "source-fixture.json")
        normalized = NormalizedFinancialDataset.model_validate(
            _load_json(source, "expected-normalized.json")
        )
        mapped = MappedFinancialDataset.model_validate(_load_json(source, "expected-mapped.json"))
        validated = ValidatedFinancialDataset.model_validate(
            _load_json(source, "expected-validated.json")
        )
        model = ThreeStatementModel.model_validate(_load_json(source, "expected-model.json"))

        assert source_fixture["entity_name"] == "Fixture Co"
        assert source_fixture["records"]
        assert normalized.schema_version == CONTRACT_SCHEMA_VERSION
        assert mapped.schema_version == CONTRACT_SCHEMA_VERSION
        assert validated.schema_version == CONTRACT_SCHEMA_VERSION
        assert model.schema_version == CONTRACT_SCHEMA_VERSION
        assert normalized.entity_name == mapped.entity_name == model.entity_name


def test_conformance_fixture_generator_matches_committed_artifacts() -> None:
    """Generated reference outputs match committed conformance fixtures exactly."""
    generator = _load_conformance_generator()

    assert generator.check_fixtures() == []
    for relative_path, content in generator.render_fixtures().items():
        assert (CONFORMANCE_DIR / relative_path).read_text() == content


def test_conformance_diagnostics_are_machine_readable() -> None:
    """Diagnostics summaries expose stable issue fields for non-Python consumers."""
    for source in SOURCES:
        diagnostics = _load_json(source, "expected-diagnostics.json")

        assert diagnostics["schema_version"] == CONTRACT_SCHEMA_VERSION
        assert diagnostics["source"] == source
        assert isinstance(diagnostics["validated_issue_codes"], list)
        assert isinstance(diagnostics["model_issue_codes"], list)
        assert isinstance(diagnostics["issues"], list)
        for issue in diagnostics["issues"]:
            parsed = ValidationIssue.model_validate(issue)
            assert parsed.code
            assert parsed.severity
            assert "metadata" in issue


def test_conformance_model_outputs_preserve_representative_values() -> None:
    """Golden model outputs preserve expected statement names and check values."""
    for source in SOURCES:
        model = ThreeStatementModel.model_validate(_load_json(source, "expected-model.json"))

        assert model.income_statement.name == "Income Statement"
        assert model.balance_sheet.name == "Balance Sheet"
        assert model.cash_flow_statement.name == "Cash Flow Statement"
        assert _line_value(model.income_statement.lines, "Revenue", "2024") == Decimal("1200")
        assert _line_value(model.income_statement.lines, "Net Income", "2024") == Decimal("316")
        assert _line_value(model.balance_sheet.lines, "Balance Check", "2024") == Decimal("0")
        assert _line_value(model.cash_flow_statement.lines, "Cash Flow Tie-Out", "2024") == Decimal(
            "0"
        )


def _line_value(lines: list[Any], label: str, period: str) -> Decimal:
    for line in lines:
        if line.label == label:
            return line.values[period]
    raise AssertionError(f"Missing statement line {label!r}.")


def _load_json(source: str, filename: str) -> Any:
    return json.loads((CONFORMANCE_DIR / source / filename).read_text())


def _load_conformance_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("waccy_conformance_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load conformance generator.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
