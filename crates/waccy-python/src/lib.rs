use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_polars::PyDataFrame;
use waccy_core::query::{statement_to_dataframe, QueryEngine};

fn to_py_err(e: impl std::fmt::Display) -> PyErr {
    pyo3::exceptions::PyRuntimeError::new_err(e.to_string())
}

fn data_dir_path(data_dir: Option<String>) -> std::path::PathBuf {
    data_dir
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|| {
            dirs_next::home_dir()
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join(".waccy")
        })
}

fn period_filter(period: Option<&str>) -> String {
    match period {
        Some(p) => format!(" AND period_label = '{}'", p.replace('\'', "''")),
        None => String::new(),
    }
}

fn run_sql(data_dir: Option<String>, sql: &str) -> PyResult<PyDataFrame> {
    let dir = data_dir_path(data_dir);
    let mut engine = QueryEngine::open(&dir).map_err(to_py_err)?;
    let df = engine.execute(sql).map_err(to_py_err)?;
    Ok(PyDataFrame(df))
}

// ── Extraction ────────────────────────────────────────────────────────────────

/// Normalise an SEC EDGAR companyfacts JSON payload into WACCY ``ExtractedData``.
///
/// Returns JSON-encoded ``ExtractedData``. Pass directly to :func:`build_model`.
#[pyfunction]
#[pyo3(signature = (companyfacts_json, periods=4, taxonomy=None))]
fn extract_edgar(
    companyfacts_json: String,
    periods: usize,
    taxonomy: Option<String>,
) -> PyResult<String> {
    let value: serde_json::Value = serde_json::from_str(&companyfacts_json).map_err(to_py_err)?;
    let taxonomy = taxonomy.as_deref().unwrap_or("us-gaap");
    let data = waccy_core::extraction::edgar::normalize_companyfacts(&value, periods, taxonomy)
        .map_err(to_py_err)?;
    serde_json::to_string(&data).map_err(to_py_err)
}

/// Normalise a raw QuickBooks Online report payload into WACCY ``ExtractedData``.
///
/// Returns JSON-encoded ``ExtractedData``. Pass directly to :func:`build_model`.
#[pyfunction]
fn extract_qbo(payload_json: String) -> PyResult<String> {
    let value: serde_json::Value = serde_json::from_str(&payload_json).map_err(to_py_err)?;
    let data = waccy_core::extraction::qbo::normalize_qbo_reports(&value).map_err(to_py_err)?;
    serde_json::to_string(&data).map_err(to_py_err)
}

// ── Modelling ─────────────────────────────────────────────────────────────────

/// Build a three-statement financial model from JSON-encoded ``ExtractedData``.
///
/// Runs the full normalize → map → validate → model pipeline and returns a
/// ``dict`` of three ``polars.DataFrame`` objects, one per statement:
///
/// .. code-block:: python
///
///     model = waccy.build_model(data_json)
///     income_df  = model["income_statement"]   # polars.DataFrame
///     balance_df = model["balance_sheet"]       # polars.DataFrame
///     cashflow_df = model["cash_flow_statement"] # polars.DataFrame
///
/// Each DataFrame has the schema:
/// ``label | account_id | period_label | amount | is_subtotal | is_check | source_account_ids``
///
/// To get validation issues (balance check, unmapped accounts, etc.) use
/// :func:`build_model_json` which returns the full ``ThreeStatementModel`` as JSON.
#[pyfunction]
fn build_model(py: Python<'_>, extracted_json: String) -> PyResult<Bound<'_, PyDict>> {
    use waccy_core::{
        extraction::normalize_map_validate,
        modeling::{ModelBuilder, ModelInput},
        models::ExtractedData,
    };
    let data: ExtractedData = serde_json::from_str(&extracted_json).map_err(to_py_err)?;
    let validated = normalize_map_validate(&data, &Default::default()).map_err(to_py_err)?;
    let model = ModelBuilder
        .build(ModelInput::Validated(validated), &Default::default())
        .map_err(to_py_err)?;

    let income_df = statement_to_dataframe(&model.income_statement).map_err(to_py_err)?;
    let balance_df = statement_to_dataframe(&model.balance_sheet).map_err(to_py_err)?;
    let cashflow_df = statement_to_dataframe(&model.cash_flow_statement).map_err(to_py_err)?;

    let dict = PyDict::new(py);
    dict.set_item("income_statement", PyDataFrame(income_df).into_pyobject(py)?)?;
    dict.set_item("balance_sheet", PyDataFrame(balance_df).into_pyobject(py)?)?;
    dict.set_item("cash_flow_statement", PyDataFrame(cashflow_df).into_pyobject(py)?)?;
    Ok(dict)
}

/// Build a three-statement model and return the full ``ThreeStatementModel``
/// as a JSON string.
///
/// Use this when you need validation issues, entity metadata, or the raw
/// model structure. For DataFrame access use :func:`build_model`.
#[pyfunction]
fn build_model_json(extracted_json: String) -> PyResult<String> {
    use waccy_core::{
        extraction::normalize_map_validate,
        modeling::{ModelBuilder, ModelInput},
        models::ExtractedData,
    };
    let data: ExtractedData = serde_json::from_str(&extracted_json).map_err(to_py_err)?;
    let validated = normalize_map_validate(&data, &Default::default()).map_err(to_py_err)?;
    let model = ModelBuilder
        .build(ModelInput::Validated(validated), &Default::default())
        .map_err(to_py_err)?;
    serde_json::to_string(&model).map_err(to_py_err)
}

// ── Query ─────────────────────────────────────────────────────────────────────

/// Execute arbitrary SQL against the financial dataset.
/// Returns a ``polars.DataFrame``. Call ``.to_pandas()`` to convert to pandas.
#[pyfunction]
#[pyo3(signature = (sql, data_dir=None))]
fn query(sql: String, data_dir: Option<String>) -> PyResult<PyDataFrame> {
    run_sql(data_dir, &sql)
}

/// Income statement for the modelled periods.
/// Returns a ``polars.DataFrame``.
#[pyfunction]
#[pyo3(signature = (period=None, data_dir=None))]
fn income_statement(period: Option<String>, data_dir: Option<String>) -> PyResult<PyDataFrame> {
    let sql = format!(
        "SELECT * FROM records WHERE statement_kind = 'income_statement'{} ORDER BY account_id",
        period_filter(period.as_deref())
    );
    run_sql(data_dir, &sql)
}

/// Balance sheet for the modelled periods.
/// Returns a ``polars.DataFrame``.
#[pyfunction]
#[pyo3(signature = (period=None, data_dir=None))]
fn balance_sheet(period: Option<String>, data_dir: Option<String>) -> PyResult<PyDataFrame> {
    let sql = format!(
        "SELECT * FROM records WHERE statement_kind = 'balance_sheet'{} ORDER BY account_id",
        period_filter(period.as_deref())
    );
    run_sql(data_dir, &sql)
}

/// Cash flow statement for the modelled periods.
/// Returns a ``polars.DataFrame``.
#[pyfunction]
#[pyo3(signature = (period=None, data_dir=None))]
fn cash_flow(period: Option<String>, data_dir: Option<String>) -> PyResult<PyDataFrame> {
    let sql = format!(
        "SELECT * FROM records WHERE statement_kind = 'cash_flow_statement'{} ORDER BY account_id",
        period_filter(period.as_deref())
    );
    run_sql(data_dir, &sql)
}

// ── Module ────────────────────────────────────────────────────────────────────

#[pymodule]
fn _lib(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(extract_edgar, m)?)?;
    m.add_function(wrap_pyfunction!(extract_qbo, m)?)?;
    m.add_function(wrap_pyfunction!(build_model, m)?)?;
    m.add_function(wrap_pyfunction!(build_model_json, m)?)?;
    m.add_function(wrap_pyfunction!(query, m)?)?;
    m.add_function(wrap_pyfunction!(income_statement, m)?)?;
    m.add_function(wrap_pyfunction!(balance_sheet, m)?)?;
    m.add_function(wrap_pyfunction!(cash_flow, m)?)?;
    Ok(())
}
