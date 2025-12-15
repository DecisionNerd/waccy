"""Build financial models from extracted data."""

from waccy.core.models import ExtractedData
from waccy.core.ontology import StandardChartOfAccounts


class ModelBuilder:
    """Build financial models from extracted data."""

    def __init__(self) -> None:
        """Initialize the model builder."""
        self.ontology = StandardChartOfAccounts()

    def build_three_statement_model(
        self,
        extracted_data: ExtractedData,
        forecast_periods: int = 12,
    ) -> "ThreeStatementModel":  # noqa: F821
        """Build integrated 3-statement model."""
        # TODO: Implement 3-statement model construction
        # 1. Normalize extracted data to standard accounts
        # 2. Build historical statements
        # 3. Apply forecasting logic
        # 4. Ensure balance checks
        raise NotImplementedError("3-statement model not yet implemented")

    def build_dcf_model(
        self,
        three_statement_model: "ThreeStatementModel",  # noqa: F821
        wacc: float,
        terminal_growth_rate: float,
        exit_multiple: float,
    ) -> "DCFModel":  # noqa: F821
        """Build DCF valuation model."""
        # TODO: Implement DCF model construction
        raise NotImplementedError("DCF model not yet implemented")

    def export_to_sheets(
        self,
        model: "AnyModel",  # noqa: F821
        output_path: str,
    ) -> None:
        """Export model to Google Sheets/Excel."""
        from waccy.modeling.exporters import SheetExporter

        exporter = SheetExporter()
        exporter.export(model, output_path)

