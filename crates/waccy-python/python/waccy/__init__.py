"""
waccy — intelligent financial modelling for small businesses.

Extraction
----------
>>> data_json = waccy.extract_edgar(companyfacts_json, periods=4)
>>> data_json = waccy.extract_qbo(payload_json)

Modelling
---------
``build_model`` returns a ``dict`` of three ``polars.DataFrame`` objects,
one per statement, in tidy long format (one row per line × period):

>>> model = waccy.build_model(data_json)
>>> income_df    = model["income_statement"]     # polars.DataFrame
>>> balance_df   = model["balance_sheet"]        # polars.DataFrame
>>> cashflow_df  = model["cash_flow_statement"]  # polars.DataFrame

DataFrame schema: label | account_id | period_label | amount | is_subtotal | is_check | source_account_ids

Use ``build_model_json`` when you need validation issues or entity metadata:

>>> import json
>>> model_dict = json.loads(waccy.build_model_json(data_json))
>>> issues = model_dict["validation_issues"]

Query (reads from ~/.waccy/ — written by `waccy extract`)
----------------------------------------------------------
All query functions return ``polars.DataFrame``. Call ``.to_pandas()`` to convert.

>>> df = waccy.income_statement("2024")
>>> df = waccy.balance_sheet()
>>> df = waccy.cash_flow()
>>> df = waccy.query("SELECT * FROM records LIMIT 10")
"""

from importlib.metadata import version as _version

__version__ = _version("waccy")

from waccy._lib import (
    balance_sheet,
    build_model,
    build_model_json,
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
    "build_model_json",
    # Query
    "query",
    "income_statement",
    "balance_sheet",
    "cash_flow",
]
