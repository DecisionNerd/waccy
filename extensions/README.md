# WACCY Extensions

This directory contains first-party extension packages for WACCY. Each extension is a separate Python package that can be built and published independently.

## Structure

```
extensions/
├── waccy-quickbooks/    # QuickBooks Online integration
└── waccy-edgar/         # SEC EDGAR filing parser
```

## Development Setup

### Install Extensions Locally

To work with extensions during development, install them in editable mode:

```bash
# Install all extensions
uv pip install -e extensions/waccy-quickbooks -e extensions/waccy-edgar

# Or install individually
uv pip install -e extensions/waccy-quickbooks
```

### Building Extensions

Each extension can be built independently:

```bash
# Build a specific extension
python scripts/build-extension.py waccy-quickbooks

# Build with clean
python scripts/build-extension.py waccy-quickbooks --clean
```

### Publishing Extensions

Extensions are published separately to PyPI:

```bash
# Publish to TestPyPI first
python scripts/publish-extension.py waccy-quickbooks --testpypi

# Publish to PyPI
python scripts/publish-extension.py waccy-quickbooks --token pypi-<your-token>
```

## Creating a New Extension

1. Create a new directory: `extensions/waccy-<name>/`
2. Set up the package structure:
   ```
   waccy-<name>/
   ├── pyproject.toml
   ├── README.md
   └── src/
       └── waccy_<name>/
           ├── __init__.py
           └── extractor.py
   ```
3. Implement the `Extractor` interface from `waccy.extraction.base`
4. Register the entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."waccy.extractors"]
   <name> = "waccy_<name>.extractor:<Name>Extractor"
   ```
5. Add dependency on `waccy` in `pyproject.toml`:
   ```toml
   dependencies = ["waccy>=0.0.2a"]
   ```

## Extension Package Requirements

Each extension package must:

- Have its own `pyproject.toml` with proper metadata
- Depend on `waccy` core package
- Implement the `Extractor` interface
- Register via entry points under `waccy.extractors`
- Follow the same code quality standards (ruff, mypy)
- Have its own version number (independent of core)

## Monorepo Benefits

- **Shared code standards**: All packages use the same linting and formatting
- **Easier refactoring**: Changes to core can be tested across all extensions
- **Unified versioning**: Coordinate releases across packages
- **Simplified CI/CD**: Test all packages together
- **Independent publishing**: Each package can be published separately to PyPI

