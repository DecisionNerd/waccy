# WACCY Architecture

## Overview

WACCY is designed as a core platform with a modular extension architecture. The core platform (`waccy`) provides the foundation—standardized data ontology, model generation frameworks, and extension interfaces—while extension packages (`waccy-*`) implement specific data source integrations and specialized functionality. This architecture enables:

- **Focused Core**: A simple, maintainable core platform with essential functionality
- **Modular Extensions**: Community-developed and third-party extension packages
- **Clean Separation**: Core platform logic independent of data source implementations
- **Easy Distribution**: Both core and extensions publishable to PyPI independently

## Current Implementation Status

This document describes both the intended architecture and the current scaffold. As of the v0.1.0 release candidate package set:

- `waccy` is `0.1.0`
- `waccy-quickbooks` is `0.1.1`
- `waccy-edgar` is `0.1.0`

The repository currently contains the core interfaces, public package exports, extension discovery, placeholder extractors, and build/publish tooling. The end-to-end workflow is tracked for [v0.1.0](https://github.com/DecisionNerd/waccy/milestone/1): QBO/QuickBooks and EDGAR inputs, canonical mapping, a three-statement model object, and XLSX export.

## Layered Data Contract

WACCY should keep extraction, normalization, modeling, metrics, and export as separate layers. The v0.1.0 implementation should make these contracts explicit so future model types can reuse the same normalized financial data.

```text
source extractor
  -> raw extracted data
  -> normalized financial dataset
  -> mapped financial dataset
  -> validated financial dataset
  -> model and metric builders
  -> exporters
```

### Source Extractor

An extractor is source-specific. It knows how to read QBO, EDGAR, or another system and return source records with provenance. It should not know how to build a three-statement model.

### Raw Extracted Data

Raw extracted data preserves source-native concepts: account names, account IDs, statement labels, transaction IDs, dates, periods, units, and source metadata. This layer is useful for auditability and debugging.

### Normalized Financial Dataset

The normalized financial dataset is the reusable contract between extraction and downstream analysis. It should represent source records in a consistent shape: periods, entities, accounts or concepts, amounts, units, source system, and provenance. It is still allowed to contain source-native account IDs and concepts.

This layer is what lets WACCY support future metric extraction and model types without rewriting extractors.

### Mapped Financial Dataset

The mapped dataset connects normalized records to the WACCY ontology. It adds canonical account IDs, confidence, review status, ambiguity diagnostics, and optional user overrides.

### Validated Financial Dataset

The validated dataset adds quality and reconciliation results: missing periods, unmapped accounts, balance checks, cash-flow tie-outs, and other diagnostics. Model and metric builders should consume this layer rather than raw source data.

### Model And Metric Builders

Builders should be source-agnostic. A three-statement model builder, DCF builder, SaaS metric extractor, covenant calculator, or comparables spreader should consume the validated dataset and ontology metadata rather than source-specific QBO or EDGAR structures.

### Exporters

Exporters render model or metric outputs into files or external systems. v0.1.0 targets XLSX workbook export; other output targets can be added later without changing extractor contracts.

## Data Source Strategy

WACCY keeps the core platform focused while allowing data sources to be added through extension packages. The first-party source strategy centers on QBO/QuickBooks and SEC EDGAR because they solve different parts of the small-business modeling problem.

### QBO / QuickBooks

QBO is the primary small-business accounting source. The integration should extract chart of accounts, financial statements, general ledger or transaction-level detail, and metadata needed to preserve source provenance.

Architecturally, QBO data should not be trusted blindly. Source account names and account types are useful signals, but WACCY should still map them through the standard ontology and report confidence or ambiguity.

The v0.1.0 QBO path keeps live API access and raw report normalization in `waccy-quickbooks`. Raw QBO `CompanyInfo`, `Account`, `ProfitAndLoss`, `BalanceSheet`, and `CashFlow` payloads are normalized into WACCY fixture-shaped source records before the core mapper, validator, model builder, XLSX exporter, or pandas handoff sees them.

### SEC EDGAR

EDGAR serves two architectural roles:

- a structured public-company source for comparable financial statement data
- a reference corpus for professional classification, terminology, and financial-statement patterns

For v0.1.0, deterministic EDGAR/XBRL concept mapping is enough to support the vertical slice. Pattern learning can be added later without blocking the first model-generation path.

### Modular Extensions

All other source systems should be added as modular packages that implement the same extractor contract. Examples include:

- Google Drive, Gmail, PDFs, and spreadsheets
- banking and payment systems
- CRM and sales systems
- HR and payroll systems
- ERP and inventory systems
- market data APIs
- other accounting systems such as Xero, Sage, and NetSuite

The core platform should remain source-agnostic after extraction. All sources must normalize into the shared financial dataset contract and then map into the WACCY ontology before model construction or metric extraction.

## Parsing And Classification Philosophy

WACCY should use deterministic logic wherever source structures are known:

- structured APIs for QBO and other accounting systems
- XBRL/company-facts structures for EDGAR
- explicit mappings for known account names, account types, and concepts
- formulaic financial statement construction and reconciliation

LLMs can assist where ambiguity is unavoidable:

- ambiguous account names
- incomplete context
- document interpretation
- classification suggestions
- relationship inference between source records

LLMs should not be the authority for financial calculations. They may propose classifications or explanations, but deterministic validation and reconciliation must remain the guardrails.

## Standard Ontology Architecture

The standard chart of accounts is the canonical layer between source data and model output. It should include:

- canonical account IDs and names
- account type and hierarchy
- statement placement
- normal balance and sign convention
- cash-flow section and treatment
- source aliases for QBO accounts and EDGAR/XBRL concepts
- metadata for confidence, review status, and auditability

The ontology enables:

- consistent model construction across sources
- cross-company comparison
- mapping quality measurement
- downstream model extensibility
- user review of ambiguous or unmapped accounts

Industry-specific templates can extend the ontology, but they should map back to standard parent accounts so customization does not destroy comparability.

## Project Structure

### Core Package (`waccy`)

The core package follows a standard Python package structure optimized for `uv`:

```
waccy/
├── pyproject.toml          # Core dependencies and package metadata
├── uv.lock                 # Lock file for reproducible builds
├── README.md
├── LICENSE
├── CODE_OF_CONDUCT.md
├── docs/
│   ├── 0-MISSION.md
│   ├── 1-EXPERIENCE.md
│   ├── 2-REQUIREMENTS.md
│   ├── 3-ARCHITECTURE.md
│   ├── assets/
│   ├── examples/
│   └── references/
├── src/
│   └── waccy/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── ontology.py          # Standardized chart of accounts
│       │   ├── models.py             # Core data models (Pydantic)
│       │   └── validation.py         # Data validation (Pandera)
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── base.py               # Abstract base classes for extractors
│       │   ├── registry.py           # Extension registry and discovery
│       │   └── mapper.py             # Mapping to standard ontology
│       ├── modeling/
│       │   ├── __init__.py
│       │   ├── builder.py            # Model construction logic
│       │   ├── templates.py          # Model templates
│       │   └── exporters.py          # Spreadsheet export
│       ├── classification/
│       │   ├── __init__.py
│       │   ├── engine.py             # LLM-enhanced classification
│       │   ├── patterns.py           # Pattern matching from EDGAR
│       │   └── confidence.py         # Confidence scoring
│       └── utils/
│           ├── __init__.py
│           ├── dates.py
│           ├── formatting.py
│           └── validation.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── scripts/
    └── publish.py                   # PyPI publishing helper
```

### Extension Packages (`waccy-*`)

Extension packages follow a consistent naming convention and structure:

```
waccy-quickbooks/
├── pyproject.toml
├── README.md
├── src/
│   └── waccy_quickbooks/
│       ├── __init__.py
│       ├── extractor.py             # Implements waccy.extraction.base.Extractor
│       └── ...
└── dist/

waccy-edgar/
├── pyproject.toml
├── README.md
├── src/
│   └── waccy_edgar/
│       ├── __init__.py
│       ├── extractor.py             # Implements waccy.extraction.base.Extractor
│       └── ...
└── dist/
```

Future extension packages may add clients, parsers, mappers, and tests as implementation grows. Those files should be added when the corresponding integration work lands.

## Package Configuration

### Core Package (`waccy`) pyproject.toml

```toml
[project]
name = "waccy"
version = "0.1.0"
description = "Intelligent financial modeling platform for small businesses"
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [
    { name = "WACCY Contributors" }
]
keywords = ["finance", "financial-modeling", "accounting", "valuation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.13",
    "Topic :: Office/Business :: Financial",
]

dependencies = [
    "numpy>=2.3.5",
    "pandas>=3.0.2",
    "pandera>=0.27.0",
    "polars>=1.36.1",
    "pydantic>=2.12.5",
    # LLM providers (modular, user installs what they need)
    # "openai>=1.0.0",  # Optional
    # "anthropic>=0.34.0",  # Optional
]

[project.optional-dependencies]
# Core extensions (maintained by WACCY team)
quickbooks = ["waccy-quickbooks>=0.1.1"]
edgar = ["waccy-edgar>=0.1.0"]
# Community extensions listed in docs but not as dependencies

[project.scripts]
waccy = "waccy.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=9.0.2",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
    "TCH", # flake8-type-checking
    "PTH", # flake8-use-pathlib
    "ERA", # eradicate
    "PL",  # Pylint
    "PERF", # Perflint
    "RET", # flake8-return
    "RUF", # Ruff-specific rules
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "PLR0913", # too many arguments (sometimes necessary)
    "PLR2004", # magic value (sometimes acceptable)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.ruff.lint.isort]
known-first-party = ["waccy"]

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Extension Package pyproject.toml Template

```toml
[project]
name = "waccy-{name}"
version = "0.0.1"
description = "WACCY extension for {description}"
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
dependencies = [
    "waccy>=0.1.0",  # Core platform dependency
    # Extension-specific dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Same ruff/mypy config as core
[tool.ruff]
# ... (same as core)

[tool.mypy]
# ... (same as core)
```

## Core Architecture Components

### 1. Extension Registry and Discovery

Extensions are discovered through Python entry points, allowing dynamic loading without requiring core platform modifications.

**`src/waccy/extraction/registry.py`**:

```python
from typing import Protocol, Type, Optional
from importlib.metadata import entry_points

class ExtractorProtocol(Protocol):
    """Protocol that all extractors must implement"""
    name: str
    data_source: str
    
    def extract(self, config: dict) -> "ExtractedData":
        ...

class ExtractorRegistry:
    """Registry for discovering and managing data source extractors"""
    
    def __init__(self):
        self._extractors: dict[str, Type[ExtractorProtocol]] = {}
        self._load_extensions()
    
    def _load_extensions(self):
        """Discover extensions via entry points"""
        discovered = entry_points(group="waccy.extractors")
        for ep in discovered:
            try:
                extractor_class = ep.load()
            except (ImportError, ModuleNotFoundError):
                continue
            instance = extractor_class()
            self._extractors[instance.data_source] = extractor_class
    
    def get_extractor(self, data_source: str) -> Optional[Type[ExtractorProtocol]]:
        """Get extractor class for a data source"""
        return self._extractors.get(data_source)
    
    def list_extractors(self) -> list[str]:
        """List all available data sources"""
        return list(self._extractors.keys())
```

**Extension entry point registration** (in extension's `pyproject.toml`):

```toml
[project.entry-points."waccy.extractors"]
quickbooks = "waccy_quickbooks.extractor:QuickBooksExtractor"
```

### 2. Standardized Ontology

The core ontology defines the standard chart of accounts and account hierarchies.

**`src/waccy/core/ontology.py`**:

```python
from enum import Enum
from typing import Literal
from pydantic import BaseModel

class AccountType(str, Enum):
    """Top-level account categories"""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class AccountCategory(BaseModel):
    """Standard account category"""
    id: str
    name: str
    type: AccountType
    parent_id: Optional[str] = None
    level: int
    description: str

class StandardChartOfAccounts:
    """WACCY standardized chart of accounts"""
    
    def __init__(self):
        self.accounts: dict[str, AccountCategory] = {}
        self._initialize_standard_accounts()
    
    def _initialize_standard_accounts(self):
        """Initialize the standard chart of accounts"""
        # Income statement accounts
        # Balance sheet accounts
        # Cash flow accounts
        # Supporting schedules
        ...
    
    def map_account(self, source_account: str, source_system: str) -> Optional[AccountCategory]:
        """Map a source account to standard account"""
        ...
```

### 3. Base Extractor Interface

All extensions must implement the base extractor interface.

**`src/waccy/extraction/base.py`**:

```python
from abc import ABC, abstractmethod
from typing import Protocol
from pydantic import BaseModel

class ExtractedTransaction(BaseModel):
    """Standard transaction format"""
    date: date
    account_id: str  # Mapped to WACCY standard
    amount: Decimal
    description: str
    source_id: str
    confidence: float  # Mapping confidence score

class ExtractedData(BaseModel):
    """Standard extracted data format"""
    transactions: list[ExtractedTransaction]
    accounts: list[AccountCategory]
    metadata: dict[str, Any]
    quality_score: float

class Extractor(ABC):
    """Abstract base class for all data source extractors"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Extractor name"""
        ...
    
    @property
    @abstractmethod
    def data_source(self) -> str:
        """Data source identifier (e.g., 'quickbooks', 'edgar')"""
        ...
    
    @abstractmethod
    def authenticate(self, credentials: dict) -> bool:
        """Authenticate with the data source"""
        ...
    
    @abstractmethod
    def extract(self, config: dict) -> ExtractedData:
        """Extract data from the source"""
        ...
    
    def validate(self, data: ExtractedData) -> bool:
        """Validate extracted data"""
        # Default implementation using Pandera
        ...
```

### 4. Classification Engine

LLM-enhanced classification for ambiguous account mappings.

**`src/waccy/classification/engine.py`**:

```python
from typing import Optional
from waccy.core.ontology import StandardChartOfAccounts

class ClassificationEngine:
    """LLM-powered classification for ambiguous accounts"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        self.ontology = StandardChartOfAccounts()
        self.llm_provider = llm_provider
    
    def classify_account(
        self, 
        source_account_name: str,
        transaction_patterns: list[dict],
        context: dict
    ) -> tuple[AccountCategory, float]:
        """Classify an ambiguous account with confidence score"""
        # 1. Try deterministic mapping first
        # 2. If ambiguous, use LLM with pattern analysis
        # 3. Validate against learned patterns from EDGAR
        ...
    
    def learn_from_edgar(self, filing_data: dict):
        """Extract classification patterns from EDGAR filings"""
        ...
```

### 5. Model Builder

Core model construction logic that works with standardized data.

**`src/waccy/modeling/builder.py`**:

```python
from waccy.extraction.base import ExtractedData
from waccy.core.ontology import StandardChartOfAccounts

class ModelBuilder:
    """Build financial models from extracted data"""
    
    def __init__(self):
        self.ontology = StandardChartOfAccounts()
    
    def build_three_statement_model(
        self, 
        extracted_data: ExtractedData,
        forecast_periods: int = 12
    ) -> "ThreeStatementModel":
        """Build integrated 3-statement model"""
        # 1. Normalize extracted data to standard accounts
        # 2. Build historical statements
        # 3. Apply forecasting logic
        # 4. Ensure balance checks
        raise NotImplementedError("3-statement model not yet implemented")
    
    def export_to_sheets(
        self, 
        model: "ThreeStatementModel",
        output_path: str
    ):
        """Export model to spreadsheet output."""
        ...
```

## Extension Development Guide

### Creating a New Extension

1. **Create package structure**:
```bash
mkdir waccy-{name}
cd waccy-{name}
uv init --name waccy_{name} --package
```

2. **Add core dependency**:
```toml
dependencies = ["waccy>=0.1.0"]
```

3. **Implement Extractor**:
```python
# src/waccy_{name}/extractor.py
from waccy.extraction.base import Extractor, ExtractedData

class MyDataSourceExtractor(Extractor):
    name = "My Data Source"
    data_source = "mydatasource"
    
    def authenticate(self, credentials: dict) -> bool:
        # Implement authentication
        ...
    
    def extract(self, config: dict) -> ExtractedData:
        # Extract and return standardized data
        ...
```

4. **Register entry point**:
```toml
[project.entry-points."waccy.extractors"]
mydatasource = "waccy_mydatasource.extractor:MyDataSourceExtractor"
```

5. **Publish to PyPI**:
```bash
uv build --no-sources
uv publish --trusted-publishing always
```

## Development Workflow

### Local Development Setup

```bash
# Clone core repository
git clone https://github.com/waccy/waccy.git
cd waccy

# Install with uv
uv sync

# Install extension in development mode
cd ../waccy-quickbooks
uv sync
uv pip install -e .
```

### Code Quality

- **Ruff**: Fast linting and formatting
  ```bash
  ruff check .
  ruff format .
  ```

- **Type Checking**: MyPy for static analysis
  ```bash
  uv run mypy src/
  ```

- **Testing**: Pytest for unit and integration tests
  ```bash
  uv run pytest
  ```

### Building and Publishing

Local builds use uv directly and should disable workspace sources before
release packaging:

```bash
# Build package
uv build --no-sources

# Check upload metadata locally without uploading
uv publish --dry-run
```

Release publishing runs through `.github/workflows/publish.yml` using PyPI
Trusted Publishers and the GitHub environment `pypi`; no long-lived PyPI token
is required in GitHub secrets. Configure each PyPI project with:

| PyPI project | Owner | Repository | Workflow | Environment |
| --- | --- | --- | --- | --- |
| `waccy` | `DecisionNerd` | `waccy` | `publish.yml` | `pypi` |
| `waccy-edgar` | `DecisionNerd` | `waccy` | `publish.yml` | `pypi` |
| `waccy-quickbooks` | `DecisionNerd` | `waccy` | `publish.yml` | `pypi` |

For projects that already exist on PyPI, add the publisher under the project's
**Publishing** settings. For a first upload of a new project, create a pending
publisher from the account-level **Publishing** page. The same publisher can be
registered for multiple PyPI projects in this monorepo.

The GitHub `pypi` environment should be limited to deployments from `main`.
Add required reviewers to that environment if the release process needs an
explicit manual approval before upload.

## Dependency Management

### Core Dependencies

Core platform maintains minimal dependencies:
- **pydantic**: Data validation and models
- **pandas**: DataFrame handoff for downstream modeling outside WACCY
- **polars**: Efficient internal data manipulation where columnar performance matters
- **pandera**: Data validation schemas
- **numpy**: Numerical computations

### Extension Dependencies

Extensions manage their own dependencies:
- Each extension's `pyproject.toml` declares dependencies
- Core platform dependency (`waccy>=X.Y.Z`) is required
- Extensions should minimize dependencies to reduce conflicts

### Optional Dependencies

LLM providers are optional and user-installed:
- Users install `openai`, `anthropic`, etc. as needed
- Core platform detects available providers at runtime
- Extensions can specify preferred LLM providers

## Testing Strategy

### Core Platform Tests

```
tests/
├── unit/
│   ├── test_ontology.py
│   ├── test_classification.py
│   └── test_modeling.py
├── integration/
│   ├── test_extraction_flow.py
│   └── test_model_generation.py
└── fixtures/
    └── sample_data.json
```

### Extension Tests

Extensions include their own test suites:
- Unit tests for extraction logic
- Mock API responses for integration tests
- Validation against core platform interfaces

## Versioning Strategy

- **Core Platform**: Semantic versioning (MAJOR.MINOR.PATCH)
  - MAJOR: Breaking changes to extension interface or ontology
  - MINOR: New features, backward-compatible
  - PATCH: Bug fixes

- **Extensions**: Independent versioning
  - Can update independently of core
  - Must declare minimum core version requirement

## Distribution and Installation

### Core Installation

```bash
# Install core platform
uv pip install waccy

# Install with core extensions
uv pip install "waccy[quickbooks,edgar]"
```

### Extension Installation

```bash
# Install individual extensions
uv pip install waccy-quickbooks
uv pip install waccy-edgar

# Extensions automatically register with core platform
```

### Development Installation

```bash
# Editable install for development
uv pip install -e .

# With dev dependencies
uv sync --dev
```

## Security Considerations

- **Credentials**: Never store credentials in code or config files
- **Environment Variables**: Use environment variables or secure credential stores
- **API Keys**: Extensions should support standard credential management
- **Data Privacy**: Local-first processing where possible, clear data handling policies

## Performance Considerations

- **Polars over Pandas**: Core platform uses Polars for better performance
- **Lazy Evaluation**: Use lazy dataframes where possible
- **Caching**: Cache API responses and parsed data
- **Parallel Processing**: Support parallel extraction for multiple sources

## Future Architecture Considerations

- **Plugin System**: More sophisticated plugin architecture for model types
- **Workflow Engine**: Orchestrate multi-step data extraction and modeling
- **API Server**: Optional API server for remote access
- **Database Backend**: Optional database for data persistence
- **GraphQL Interface**: Query interface for flexible data access
