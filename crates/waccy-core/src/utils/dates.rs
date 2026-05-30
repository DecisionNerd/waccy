use chrono::NaiveDate;

use crate::{
    error::WaccyError,
    models::{PeriodType, ReportingPeriod},
};

/// Infer a `ReportingPeriod` from a common label: "2024", "2024Q1", "2024-01".
pub fn infer_reporting_period(label: &str) -> Result<ReportingPeriod, WaccyError> {
    let s = label.trim();

    // Annual: "2024"
    if let Some(year) = parse_year_only(s) {
        return Ok(ReportingPeriod {
            label: s.to_string(),
            start_date: NaiveDate::from_ymd_opt(year, 1, 1).unwrap(),
            end_date: NaiveDate::from_ymd_opt(year, 12, 31).unwrap(),
            period_type: PeriodType::Year,
        });
    }

    // FY label: "FY2024"
    if let Some(year) = s
        .to_ascii_uppercase()
        .strip_prefix("FY")
        .and_then(|y| y.parse::<i32>().ok())
    {
        return Ok(ReportingPeriod {
            label: s.to_string(),
            start_date: NaiveDate::from_ymd_opt(year, 1, 1).unwrap(),
            end_date: NaiveDate::from_ymd_opt(year, 12, 31).unwrap(),
            period_type: PeriodType::Year,
        });
    }

    // Quarter: "2024Q1" or "2024-Q1"
    if let Some((year, quarter)) = parse_quarter(s) {
        let start_month = ((quarter - 1) * 3 + 1) as u32;
        let end_month = start_month + 2;
        let end_day = days_in_month(year, end_month);
        return Ok(ReportingPeriod {
            label: format!("{year}Q{quarter}"),
            start_date: NaiveDate::from_ymd_opt(year, start_month, 1).unwrap(),
            end_date: NaiveDate::from_ymd_opt(year, end_month, end_day).unwrap(),
            period_type: PeriodType::Quarter,
        });
    }

    // Month: "2024-01" or "202401"
    if let Some((year, month)) = parse_month(s) {
        let end_day = days_in_month(year, month);
        return Ok(ReportingPeriod {
            label: format!("{year}-{month:02}"),
            start_date: NaiveDate::from_ymd_opt(year, month, 1).unwrap(),
            end_date: NaiveDate::from_ymd_opt(year, month, end_day).unwrap(),
            period_type: PeriodType::Month,
        });
    }

    Err(WaccyError::Extraction(format!(
        "Unsupported reporting period label {label:?}"
    )))
}

fn parse_year_only(s: &str) -> Option<i32> {
    if s.len() == 4 {
        s.parse().ok()
    } else {
        None
    }
}

fn parse_quarter(s: &str) -> Option<(i32, u8)> {
    // "2024Q2" or "2024-Q2"
    let upper = s.to_ascii_uppercase();
    let (year_part, q_part) = if let Some(idx) = upper.find("-Q") {
        (&s[..idx], &upper[idx + 2..])
    } else if let Some(idx) = upper.find('Q') {
        (&s[..idx], &upper[idx + 1..])
    } else {
        return None;
    };
    let year: i32 = year_part.parse().ok()?;
    let quarter: u8 = q_part.parse().ok()?;
    if (1..=4).contains(&quarter) { Some((year, quarter)) } else { None }
}

fn parse_month(s: &str) -> Option<(i32, u32)> {
    // "2024-01" or "2024-1"
    let parts: Vec<&str> = s.splitn(2, '-').collect();
    if parts.len() == 2 {
        let year: i32 = parts[0].parse().ok()?;
        let month: u32 = parts[1].parse().ok()?;
        if (1..=12).contains(&month) {
            return Some((year, month));
        }
    }
    None
}

fn days_in_month(year: i32, month: u32) -> u32 {
    let next = if month == 12 {
        NaiveDate::from_ymd_opt(year + 1, 1, 1)
    } else {
        NaiveDate::from_ymd_opt(year, month + 1, 1)
    };
    let first = NaiveDate::from_ymd_opt(year, month, 1).unwrap();
    (next.unwrap() - first).num_days() as u32
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Datelike;

    #[test]
    fn annual() {
        let p = infer_reporting_period("2024").unwrap();
        assert_eq!(p.label, "2024");
        assert_eq!(p.period_type, PeriodType::Year);
        assert_eq!(p.start_date, NaiveDate::from_ymd_opt(2024, 1, 1).unwrap());
        assert_eq!(p.end_date, NaiveDate::from_ymd_opt(2024, 12, 31).unwrap());
    }

    #[test]
    fn quarter() {
        let p = infer_reporting_period("2024Q1").unwrap();
        assert_eq!(p.label, "2024Q1");
        assert_eq!(p.period_type, PeriodType::Quarter);
        assert_eq!(p.start_date, NaiveDate::from_ymd_opt(2024, 1, 1).unwrap());
        assert_eq!(p.end_date, NaiveDate::from_ymd_opt(2024, 3, 31).unwrap());
    }

    #[test]
    fn month() {
        let p = infer_reporting_period("2024-06").unwrap();
        assert_eq!(p.label, "2024-06");
        assert_eq!(p.period_type, PeriodType::Month);
        assert_eq!(p.end_date, NaiveDate::from_ymd_opt(2024, 6, 30).unwrap());
    }

    #[test]
    fn fy_label() {
        let p = infer_reporting_period("FY2023").unwrap();
        assert_eq!(p.period_type, PeriodType::Year);
        assert_eq!(p.start_date.year(), 2023);
    }
}
