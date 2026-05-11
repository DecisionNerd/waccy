# WACCY

**Intelligent Financial Modeling Platform for Small Businesses**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<div align="center">
  <img src="waccy-logo-NoBG.png" alt="WACCY Logo" width="400"/>
</div>

WACCY is an intelligent financial modeling platform designed to automatically extract, parse, classify, and synthesize business data from diverse sources to generate sophisticated, production-grade financial models and operating analyses. **The platform's primary focus is on small businesses—from sole proprietorships to growing companies—that struggle with messy, incomplete, and poorly-maintained financial records.**

Unlike large enterprises with dedicated accounting teams, small businesses often have inconsistent record-keeping, ambiguous account classifications, incomplete data, and limited financial infrastructure. WACCY transforms this raw, often chaotic business data into comprehensive, auditable, and decision-ready financial models that adhere to institutional-quality standards.

## Current Status

WACCY is an early package, but the v0.1.0 vertical slice now implements a fixture-first financial modeling path:

* QBO/QuickBooks-shaped fixture extraction through `QuickBooksExtractor`
* a small typed QuickBooks OAuth/report puller in `waccy-quickbooks`
* EDGAR/XBRL-shaped fixture extraction through `EdgarExtractor`
* normalized, mapped, and validated financial datasets
* deterministic source-to-WACCY account mapping with override support
* three-statement model construction with reconciliation checks
* XLSX export with the three required workbook sheets
* pandas DataFrame export for follow-on modeling outside WACCY

The QuickBooks helper pulls raw QBO company info, chart of accounts, and reports, then normalizes those reports into WACCY source records. Live EDGAR fetching and richer filing parsing remain planned. The first milestone remains focused on hardening the QBO/EDGAR path into the [v0.1.0 release](https://github.com/DecisionNerd/waccy/milestone/1), tracked by [issue #15](https://github.com/DecisionNerd/waccy/issues/15).

## Quick Start

### Installation

WACCY uses `uv`, the modern Python package manager. Install the core platform:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install WACCY core platform
uv pip install waccy

# Install with core extensions (QuickBooks Online and SEC EDGAR)
uv pip install "waccy[quickbooks,edgar]"

# Or install individual extensions
uv pip install waccy-quickbooks
uv pip install waccy-edgar
```

### What Works Today

The current package can discover installed extractor entry points and build source-agnostic three-statement outputs from fixture data:

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
available_sources = registry.list_extractors()
print(f"Available data sources: {available_sources}")
```

Implemented v0.1.0 components include:

* fixture-first QBO and EDGAR extraction
* typed QBO OAuth token cache, raw report pulling, and deterministic report normalization
* standard account ontology and deterministic aliases
* mapping, validation, reconciliation, and quality diagnostics
* three-statement model building
* spreadsheet export
* pandas DataFrame handoff for external modeling workflows
* local and CI quality gates with BDD outcome specs

Still planned:

* full live QuickBooks product workflow beyond report pulling and normalization
* live EDGAR fetching and richer filing parsing
* LLM-assisted classification and confidence scoring beyond placeholders
* advanced model types such as DCF, LBO, M&A, and specialized industry models

## Planned Capabilities

### 🤖 **AI-Powered Data Extraction & Classification**

* **Intelligent Account Mapping**: LLM-enhanced classification for ambiguous account names and inconsistent categorizations
* **Missing Data Inference**: Patterns learned from high-quality sources (EDGAR filings) to infer missing information
* **Causal Chain Recognition**: Understands how financial events cascade through statements
* **Terminology Normalization**: Maps equivalent concepts across different naming conventions
* **Confidence Scoring**: Every classification includes a confidence score for quality assessment

### 🏗️ **Standardized Financial Ontology**

* **WACCY Standard Chart of Accounts**: Comprehensive, standardized classification ontology
* **Universal Mapping**: All data sources map to the same standard accounts for consistency
* **Industry Templates**: Pre-configured extensions for SaaS, manufacturing, retail, real estate, and more
* **Quality Quantification**: Standardized ontology enables measurement of data quality and model reliability

### 📊 **Institutional-Quality Financial Models**

* **3-Statement Integrated Models**: Income statement, balance sheet, and cash flow with full balancing
* **DCF Valuation Models**: Detailed free cash flow construction, terminal value analysis, WACC calculation
* **Trading Comparables**: Peer company analysis with multiple calculation and benchmarking
* **Transaction Comparables**: Precedent M&A transaction analysis
* **LBO Models**: Leveraged buyout analysis with returns calculation and debt schedules
* **M&A Models**: Accretion/dilution analysis with purchase accounting
* **Specialized Models**: SaaS cohort models, REIT models, project finance, cap tables, and more

### 🔌 **Modular Extension Architecture**

* **Core Platform**: Focused core with QuickBooks Online and SEC EDGAR as primary data sources
* **Extensible Design**: Community-developed extension packages for additional data sources
* **Entry Point Discovery**: Automatic discovery of extensions via Python entry points
* **Simple Installation**: Install only the extensions you need

### 📈 **Advanced Forecasting & Analysis**

* **Driver-Based Forecasting**: Revenue builds from price × volume, units × ARPU, cohort models
* **Working Capital Modeling**: DSO, DIO, DPO analysis with seasonality adjustments
* **Debt & Interest Modeling**: Revolver mechanics, amortization schedules, cash sweep waterfalls
* **Tax Modeling**: Effective tax rates, DTAs/DTLs, NOL utilization tracking
* **Sensitivity Analysis**: Comprehensive scenario modeling and tornado charts

### ✅ **Data Quality & Validation**

* **Pandera Validation**: Schema-based validation for extracted data
* **Mapping Confidence Scores**: Quantify the reliability of account mappings
* **Reconciliation Checks**: Cross-referencing between sources and balance checks
* **Audit Trails**: Every data point traceable to source with full provenance

### 📝 **Professional Model Outputs**

* **Spreadsheet Export**: Production-ready workbook models with proper formatting
* **Professional Architecture**: Modular tab structures, consistent time axis, clear sign conventions
* **Color Conventions**: Inputs in blue, calculations in black, outputs in green
* **Balance Checks**: Built-in reconciliation tables and error flags
* **Scenario Tooling**: Data tables for sensitivity analysis, scenario toggles, goal seek integration

## Fixture-First Workflow

The v0.1.0 workflow starts with fixture-shaped records. Live API configuration can be added later without changing the downstream modeling contract.

```python
from waccy.modeling import ModelBuilder
from waccy_quickbooks.extractor import QuickBooksExtractor

fixture = {
    "entity_name": "Example Co",
    "periods": [
        {"label": "2024", "start_date": "2024-01-01", "end_date": "2024-12-31"}
    ],
    "records": [
        {"name": "Sales", "period": "2024", "amount": 1000, "statement": "income_statement"},
        {"name": "Cost of Goods Sold", "period": "2024", "amount": 400, "statement": "income_statement"},
        {"name": "Checking", "period": "2024", "amount": 100, "statement": "balance_sheet"},
    ],
}

extracted_data = QuickBooksExtractor().extract({"fixture": fixture})
builder = ModelBuilder()
model = builder.build_three_statement_model(extracted_data)
builder.export_to_sheets(model, output_path="financial_model.xlsx")
```

## Target Output

### Standardized Account Mapping

**Source Account**: `"Sales Revenue"` (QuickBooks)  
**Mapped To**: `Revenue - Product Sales` (WACCY Standard)  
**Confidence**: 0.95  
**Validation**: ✅ Transaction patterns match revenue recognition

### v0.1.0 Workbook Structure

```text
Financial Model.xlsx
├── Income Statement
├── Balance Sheet
└── Cash Flow Statement
```

## 🔗 Core Data Sources

### QuickBooks Online (QBO)

**Primary Data Source** - The accounting system most commonly used by small businesses.

Implemented for v0.1.0:

* Fixture-first extraction path for chart of accounts and statement data
* Account normalization and source provenance
* Skeptical treatment of source classifications with validation

Planned after v0.1.0:

* Real-client path documented behind explicit credentials/configuration

### SEC EDGAR

**Pattern Learning & Reference Data** - High-quality financial data for learning and benchmarking.

Implemented for v0.1.0:

* Fixture-first extraction path for public company statement data
* Deterministic XBRL/concept mapping to WACCY accounts
* Deterministic EDGAR pattern extraction for fixture concepts and statement hints
* Period normalization and source provenance

Planned after v0.1.0:

* Live EDGAR filing fetch and full public-company fact ingestion

### Extension Packages

Additional data sources are planned as modular extensions, but they are not included in the current repository:

* `waccy-google` - Google Drive and Gmail integration
* `waccy-xero` - Xero accounting system
* `waccy-sage` - Sage accounting platform
* `waccy-stripe` - Payment processor data
* `waccy-salesforce` - CRM and sales pipeline data

## 📁 Project Structure

WACCY uses a **monorepo structure** where the core platform and first-party extensions are maintained together but built and published separately.

```
waccy/
├── src/
│   └── waccy/                       # Core platform
│       ├── core/
│       │   ├── ontology.py          # Standardized chart of accounts
│       │   ├── models.py            # Core data models (Pydantic)
│       │   └── validation.py        # Data validation (Pandera)
│       ├── extraction/
│       │   ├── base.py              # Abstract base classes
│       │   ├── registry.py          # Extension registry
│       │   └── mapper.py            # Mapping to standard ontology
│       ├── classification/
│       │   ├── engine.py            # LLM-enhanced classification
│       │   ├── patterns.py          # Pattern matching from EDGAR
│       │   └── confidence.py        # Confidence scoring
│       ├── modeling/
│       │   ├── builder.py           # Model construction
│       │   ├── templates.py         # Model templates
│       │   └── exporters.py         # Spreadsheet export
│       └── utils/
│           ├── dates.py
│           ├── formatting.py
│           └── validation.py
├── extensions/                      # First-party extensions (monorepo)
│   ├── waccy-quickbooks/            # QuickBooks Online integration
│   │   ├── src/waccy_quickbooks/
│   │   └── pyproject.toml
│   └── waccy-edgar/                 # SEC EDGAR filing parser
│       ├── src/waccy_edgar/
│       └── pyproject.toml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
│   ├── publish.py                   # Publish core package
│   ├── build-extension.py          # Build extension packages
│   └── publish-extension.py        # Publish extension packages
├── docs/
│   ├── 0-MISSION.md
│   ├── 1-EXPERIENCE.md
│   ├── 2-REQUIREMENTS.md
│   ├── 3-ARCHITECTURE.md
│   ├── assets/
│   ├── examples/
│   └── references/
└── pyproject.toml                   # Core package configuration
```

### Monorepo Benefits

- **Unified Development**: All packages in one repository for easier coordination
- **Independent Publishing**: Each package builds and publishes separately to PyPI
- **Shared Standards**: Consistent code quality, linting, and testing across packages
- **Easier Refactoring**: Changes to core can be tested with all extensions immediately

See [extensions/README.md](extensions/README.md) for details on working with extensions.

## 🧪 Testing

```bash
# Install development dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=waccy --cov-report=html

# Run specific test suites
uv run pytest tests/unit/
uv run pytest tests/integration/

# Format and lint with ruff
uv run ruff format
uv run ruff check --fix

# Type checking with mypy
uv run mypy src/waccy
```

## 📚 Documentation

Published docs: <https://decisionnerd.github.io/waccy/>

* **[Mission Statement](docs/0-MISSION.md)** - Project goals, philosophy, and roadmap
* **[Experience](docs/1-EXPERIENCE.md)** - Target user workflows and release experience
* **[Requirements](docs/2-REQUIREMENTS.md)** - Financial modeling requirements and capabilities
* **[Architecture](docs/3-ARCHITECTURE.md)** - Technical architecture and design principles
* **[Testing](docs/4-TESTING.md)** - Quality gates, BDD outcomes, and coverage expectations

## 🏛️ Design Principles

1. **Simplicity and Focus**: Core platform maintains a simple, focused design with essential data sources (QBO and EDGAR)

2. **Standardized Ontology First**: All financial data maps to a standardized WACCY chart of accounts, ensuring consistency and comparability

3. **Modular Extensibility**: New data sources and model types added as separate packages that conform to core interfaces

4. **Accuracy First**: Deterministic functions preferred over probabilistic models. LLMs used for parsing and classification, not financial calculations

5. **Transparency and Auditability**: Every data point traceable to source, every calculation explainable, every assumption documented

6. **Professional Standards**: Models adhere to institutional-quality standards for architecture, formatting, and presentation

7. **Quality Quantification**: Standardized ontology enables measurement and reporting of data quality and model output reliability

8. **Small Business Focus**: Designed primarily for small businesses—from sole proprietorships to growing companies—handling messy, incomplete data

## 🤝 Contributing

We welcome contributions! WACCY is built for the small business community, and we'd love your help making financial modeling more accessible.

### Getting Started

1. **Fork the repository** on GitHub
2. **Create a feature branch** for your contribution
3. **Set up development environment**:
   ```bash
   git clone https://github.com/your-username/waccy.git
   cd waccy
   uv sync --dev
   ```
4. **Make your changes** following our coding standards:
   - Use `ruff` for formatting and linting
   - Add type hints with `mypy` compliance
   - Write tests for new functionality
   - Update documentation as needed
5. **Run tests and linting**:
   ```bash
   uv run pytest
   uv run ruff check
   uv run mypy src/
   ```
6. **Submit a pull request** with a clear description of your changes

### Creating Extensions

Want to add a new data source? Create an extension package:

1. Create a new package: `waccy-yourdatasource`
2. Implement the `Extractor` interface from `waccy.extraction.base`
3. Register your extension via entry points
4. Follow the [Extension Development Guide](docs/3-ARCHITECTURE.md#extension-development-guide)

See our [Architecture Documentation](docs/3-ARCHITECTURE.md) for detailed extension development guidelines.

### Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming environment for all contributors.

## Project Status

* **Release candidate core**: `waccy 0.1.0`
* **Release candidate first-party extensions**: `waccy-quickbooks 0.1.1`, `waccy-edgar 0.1.0`
* **Current implementation**: fixture-first v0.1.0 three-statement pipeline with QBO report normalization, EDGAR companyfacts normalization, XLSX export, and pandas handoff
* **Current milestone**: [v0.1.0](https://github.com/DecisionNerd/waccy/milestone/1), with all tracked release-validity issues closed

Planned phases:

* **Phase 1**: Core foundation and three-statement models
* **Phase 2**: Public market data and richer pattern learning
* **Phase 3**: Advanced valuation models
* **Phase 4**: Specialized model types
* **Phase 5**: Advanced analysis and decision support

**Python Version**: 3.13+  
**Package Manager**: [uv](https://github.com/astral-sh/uv)  
**CI/CD**: GitHub Actions, Codecov, and CodeRabbit

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

* **Small Business Community** - Built for entrepreneurs and small business owners who need professional financial modeling
* **Financial Modeling Community** - Inspired by institutional-quality modeling standards
* **Open Source Tools**: 
  * [uv](https://github.com/astral-sh/uv) - Modern Python package manager
  * [ruff](https://github.com/astral-sh/ruff) - Fast Python linter and formatter
  * [Pydantic](https://github.com/pydantic/pydantic) - Data validation framework
  * [pandas](https://github.com/pandas-dev/pandas) - DataFrame handoff for downstream modeling
  * [Polars](https://github.com/pola-rs/polars) - High-performance data manipulation
  * [Pandera](https://github.com/pandera-dev/pandera) - Statistical data validation

---

**Made with 🤪 for small businesses that deserve institutional-quality financial modeling**
