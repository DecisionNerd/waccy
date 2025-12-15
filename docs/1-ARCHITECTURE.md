# WACCY Architecture

## Overview

WACCY is designed as a core platform with a modular extension architecture. The core platform (`waccy`) provides the foundation—standardized data ontology, model generation frameworks, and extension interfaces—while extension packages (`waccy-*`) implement specific data source integrations and specialized functionality. This architecture enables:

- **Focused Core**: A simple, maintainable core platform with essential functionality
- **Modular Extensions**: Community-developed and third-party extension packages
- **Clean Separation**: Core platform logic independent of data source implementations
- **Easy Distribution**: Both core and extensions publishable to PyPI independently

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
│   ├── 1-ARCHITECTURE.md
│   ├── 2-EXPERIENCE.md
│   └── skills_models.md
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
│       │   └── exporters.py          # Google Sheets export
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
├── uv.lock
├── README.md
├── src/
│   └── waccy_quickbooks/
│       ├── __init__.py
│       ├── client.py                # QuickBooks API client
│       ├── extractor.py             # Implements waccy.extraction.base.Extractor
│       └── mapper.py                # QBO-specific mappings
└── tests/

waccy-edgar/
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
│   └── waccy_edgar/
│       ├── __init__.py
│       ├── client.py                # SEC EDGAR API client
│       ├── extractor.py             # Filing parser and extractor
│       ├── parser.py                # 10-K, 10-Q parsing
│       └── patterns.py              # Pattern extraction for learning
└── tests/

waccy-google/
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
│   └── waccy_google/
│       ├── __init__.py
│       ├── drive.py                 # Google Drive integration
│       ├── gmail.py                 # Gmail integration
│       └── extractor.py             # Document/email extractor
└── tests/
```

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
    "pandera>=0.27.0",
    "polars>=1.36.1",
    "pydantic>=2.12.5",
    # LLM providers (modular, user installs what they need)
    # "openai>=1.0.0",  # Optional
    # "anthropic>=0.34.0",  # Optional
]

[project.optional-dependencies]
# Core extensions (maintained by WACCY team)
quickbooks = ["waccy-quickbooks>=0.1.0"]
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
version = "0.1.0"
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
            extractor_class = ep.load()
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
        ...
    
    def export_to_sheets(
        self, 
        model: "ThreeStatementModel",
        output_path: str
    ):
        """Export model to Google Sheets"""
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
uv build
uv publish
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

```bash
# Build package
uv build

# Publish to PyPI (requires credentials)
uv publish
```

## Dependency Management

### Core Dependencies

Core platform maintains minimal dependencies:
- **pydantic**: Data validation and models
- **polars**: Efficient data manipulation (preferred over pandas for performance)
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
