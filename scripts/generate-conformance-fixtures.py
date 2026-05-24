"""Generate cross-language conformance fixtures from the Python reference path."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from waccy.core.models import (
    CONTRACT_SCHEMA_VERSION,
    ExtractedData,
    ThreeStatementModel,
    ValidatedFinancialDataset,
)
from waccy.extraction.mapper import DataMapper, source_record_from_dict
from waccy.modeling.builder import ModelBuilder

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE_DIR = ROOT / "tests" / "conformance"
SAMPLE_DATA_PATH = ROOT / "tests" / "fixtures" / "sample_data.py"

if TYPE_CHECKING:
    from pydantic import BaseModel


def _sample_qbo_fixture() -> dict[str, Any]:
    return _load_sample_fixture("sample_qbo_fixture")


def _sample_edgar_fixture() -> dict[str, Any]:
    return _load_sample_fixture("sample_edgar_fixture")


def _load_sample_fixture(function_name: str) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("waccy_sample_data", SAMPLE_DATA_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load sample data fixtures.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = getattr(module, function_name)()
    if not isinstance(fixture, dict):
        raise TypeError(f"Sample fixture {function_name!r} must return a dictionary.")
    return fixture


SOURCE_FIXTURES: dict[str, Any] = {
    "qbo": _sample_qbo_fixture,
    "edgar": _sample_edgar_fixture,
}


def _json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _model_json(model: BaseModel) -> str:
    return _json_dumps(model.model_dump(mode="json"))


def _source_json(source_fixture: dict[str, Any]) -> str:
    return _json_dumps(source_fixture)


def _extracted(source: str, source_fixture: dict[str, Any]) -> ExtractedData:
    if "records" not in source_fixture:
        raise ValueError(f"Conformance source fixture {source!r} is missing 'records'.")
    if "entity_name" not in source_fixture:
        raise ValueError(f"Conformance source fixture {source!r} is missing 'entity_name'.")
    raw_records = source_fixture["records"]
    if not isinstance(raw_records, list):
        raise ValueError(f"Conformance source fixture {source!r} records must be a list.")
    entity_name = source_fixture["entity_name"]
    if not isinstance(entity_name, str):
        raise ValueError(f"Conformance source fixture {source!r} entity_name must be a string.")
    records = []
    for record in raw_records:
        if not isinstance(record, dict):
            raise ValueError(f"Conformance source fixture {source!r} records must be objects.")
        records.append(source_record_from_dict(record, source))
    return ExtractedData(
        entity_name=entity_name,
        source_records=records,
        metadata={"source": source},
    )


def _diagnostics_json(
    source: str,
    validated: ValidatedFinancialDataset,
    model: ThreeStatementModel,
) -> str:
    validated_issues = [issue.model_dump(mode="json") for issue in validated.issues]
    model_issues = [issue.model_dump(mode="json") for issue in model.validation_issues]
    all_issues = [*validated_issues, *model_issues]
    return _json_dumps(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "source": source,
            "validated_issue_codes": [issue["code"] for issue in validated_issues],
            "model_issue_codes": [issue["code"] for issue in model_issues],
            "issues": all_issues,
        }
    )


def build_case(source: str) -> dict[str, str]:
    """Return deterministic JSON artifacts for one conformance source."""
    if source not in SOURCE_FIXTURES:
        valid = ", ".join(sorted(SOURCE_FIXTURES))
        raise ValueError(f"Unknown conformance source {source!r}. Valid sources: {valid}.")
    source_fixture = SOURCE_FIXTURES[source]()
    mapper = DataMapper()
    extracted = _extracted(source, source_fixture)
    normalized = mapper.normalize(extracted)
    mapped = mapper.map_dataset(normalized)
    validated = mapper.validate(mapped)
    model = ModelBuilder().build_three_statement_model(validated)

    return {
        "source-fixture.json": _source_json(source_fixture),
        "expected-normalized.json": _model_json(normalized),
        "expected-mapped.json": _model_json(mapped),
        "expected-validated.json": _model_json(validated),
        "expected-model.json": _model_json(model),
        "expected-diagnostics.json": _diagnostics_json(source, validated, model),
    }


def render_fixtures() -> dict[Path, str]:
    """Return deterministic fixture contents keyed by repo-relative path."""
    artifacts: dict[Path, str] = {}
    for source in sorted(SOURCE_FIXTURES):
        for filename, content in build_case(source).items():
            artifacts[Path(source) / filename] = content
    return artifacts


def write_fixtures() -> None:
    """Write generated conformance fixtures to tests/conformance."""
    for relative_path, content in render_fixtures().items():
        path = CONFORMANCE_DIR / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def check_fixtures() -> list[str]:
    """Return repo-relative fixture paths that differ from generated output."""
    mismatches = []
    for relative_path, content in render_fixtures().items():
        path = CONFORMANCE_DIR / relative_path
        if not path.exists() or path.read_text() != content:
            mismatches.append(str(path.relative_to(ROOT)))
    return mismatches


def main() -> int:
    """Run the conformance fixture generator or drift check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed conformance fixtures differ from generated output",
    )
    args = parser.parse_args()

    if args.check:
        mismatches = check_fixtures()
        if mismatches:
            joined = ", ".join(mismatches)
            print(f"Conformance fixtures are out of date: {joined}")
            return 1
        print("Conformance fixtures are current.")
        return 0

    write_fixtures()
    print(f"Wrote conformance fixtures to {CONFORMANCE_DIR.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
