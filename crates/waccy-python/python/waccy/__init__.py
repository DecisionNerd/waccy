"""
waccy — intelligent financial modelling for small businesses.

Extraction
----------
>>> import json
>>> data_json = waccy.extract_edgar(companyfacts_json, periods=4)
>>> data_json = waccy.extract_qbo(payload_json)

Modelling
---------
>>> model_json = waccy.build_model(data_json)
>>> model = json.loads(model_json)

Query (returns polars.DataFrame)
---------------------------------
>>> df = waccy.income_statement("2024")
>>> df = waccy.balance_sheet()
>>> df = waccy.cash_flow()
>>> df = waccy.query("SELECT * FROM records LIMIT 10")

# Convert to pandas if needed
>>> pandas_df = df.to_pandas()

Note on extraction
------------------
The CLI tool (``waccy extract``) writes results to ``~/.waccy/``.
The Python query functions read from that directory by default.
Pass ``data_dir=`` to override.
"""

from importlib.metadata import version as _version

__version__ = _version("waccy")

from waccy._lib import (
    balance_sheet,
    build_model,
    cash_flow,
    extract_edgar,
    extract_qbo,
    income_statement,
    query,
)

__all__ = [
    # Extraction
    "extract_edgar",
    "extract_qbo",
    # Modelling
    "build_model",
    # Query
    "query",
    "income_statement",
    "balance_sheet",
    "cash_flow",
]
