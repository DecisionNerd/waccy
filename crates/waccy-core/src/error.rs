use thiserror::Error;

#[derive(Debug, Error)]
pub enum WaccyError {
    #[error("extraction error: {0}")]
    Extraction(String),

    #[error("classification error: {0}")]
    Classification(String),

    #[error("modeling error: {0}")]
    Modeling(String),

    #[error("query error: {0}")]
    Query(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("serialisation error: {0}")]
    Serialisation(#[from] serde_json::Error),

    #[error("polars error: {0}")]
    Polars(#[from] polars::error::PolarsError),
}
