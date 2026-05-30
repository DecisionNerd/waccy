use std::collections::HashMap;
use std::sync::LazyLock;

use crate::models::{AccountType, CashFlowSection, NormalBalance, StandardAccount, StatementKind};

fn key(s: &str) -> String {
    s.chars()
        .filter(|c| c.is_alphanumeric())
        .flat_map(|c| c.to_lowercase())
        .collect()
}

pub struct StandardChartOfAccounts {
    pub accounts: HashMap<String, StandardAccount>,
    // normalized key → list of account ids
    aliases: HashMap<String, Vec<String>>,
}

impl StandardChartOfAccounts {
    fn new() -> Self {
        let mut chart = Self {
            accounts: HashMap::new(),
            aliases: HashMap::new(),
        };
        chart.init();
        chart
    }

    fn add(&mut self, account: StandardAccount) {
        // Index by id and name
        self.aliases
            .entry(key(&account.id))
            .or_default()
            .push(account.id.clone());
        self.aliases
            .entry(key(&account.name))
            .or_default()
            .push(account.id.clone());
        for alias in &account.aliases {
            self.aliases
                .entry(key(alias))
                .or_default()
                .push(account.id.clone());
        }
        self.accounts.insert(account.id.clone(), account);
    }

    pub fn map_candidates(&self, source_account: &str) -> Vec<&StandardAccount> {
        let k = key(source_account);
        let ids = match self.aliases.get(&k) {
            Some(ids) => ids,
            None => return vec![],
        };
        // deduplicate while preserving order
        let mut seen = std::collections::HashSet::new();
        ids.iter()
            .filter(|id| seen.insert(*id))
            .filter_map(|id| self.accounts.get(id))
            .collect()
    }

    pub fn map_account(&self, source_account: &str) -> Option<&StandardAccount> {
        let candidates = self.map_candidates(source_account);
        if candidates.len() == 1 { Some(candidates[0]) } else { None }
    }

    pub fn get(&self, id: &str) -> Option<&StandardAccount> {
        self.accounts.get(id)
    }

    pub fn list(&self) -> Vec<&StandardAccount> {
        let mut accounts: Vec<_> = self.accounts.values().collect();
        accounts.sort_by_key(|a| a.sort_order);
        accounts
    }

    fn init(&mut self) {
        let specs: &[(&str, &str, AccountType, StatementKind, NormalBalance, Option<CashFlowSection>, u32, &[&str])] = &[
            ("revenue", "Revenue", AccountType::Revenue, StatementKind::IncomeStatement, NormalBalance::Credit, None, 100, &[
                "sales", "sales revenue", "total revenue", "income",
                "us-gaap:revenues",
                "us-gaap:revenuefromcontractwithcustomerexcludingassessedtax",
                "us-gaap:salesrevenuenet",
                "revenues",
            ]),
            ("cogs", "Cost of Goods Sold", AccountType::Expense, StatementKind::IncomeStatement, NormalBalance::Debit, None, 200, &[
                "cost of goods sold", "cost of revenue", "cost of sales",
                "us-gaap:costofrevenue",
                "us-gaap:costofgoodsandservicessold",
                "us-gaap:costofgoodsandserviceexcludingdepreciationdepletionandamortization",
            ]),
            ("operating_expenses", "Operating Expenses", AccountType::Expense, StatementKind::IncomeStatement, NormalBalance::Debit, None, 300, &[
                "opex", "operating expense", "operating expenses",
                "general and administrative", "sg&a",
                "us-gaap:operatingexpenses",
                "us-gaap:sellinggeneralandadministrativeexpense",
            ]),
            ("depreciation_amortization", "Depreciation & Amortization", AccountType::Expense, StatementKind::IncomeStatement, NormalBalance::Debit, None, 350, &[
                "depreciation", "amortization", "d&a",
                "us-gaap:depreciationdepletionandamortization",
                "us-gaap:depreciationdepletionandamortizationexpense",
            ]),
            ("interest_expense", "Interest Expense", AccountType::Expense, StatementKind::IncomeStatement, NormalBalance::Debit, None, 400, &[
                "interest", "interest expense",
                "us-gaap:interestexpense",
                "us-gaap:interestexpensenonoperating",
            ]),
            ("tax_expense", "Tax Expense", AccountType::Expense, StatementKind::IncomeStatement, NormalBalance::Debit, None, 500, &[
                "tax", "income tax", "income tax expense",
                "us-gaap:incometaxexpensebenefit",
            ]),
            ("cash", "Cash", AccountType::Asset, StatementKind::BalanceSheet, NormalBalance::Debit, None, 1000, &[
                "bank", "cash and cash equivalents", "checking", "savings",
                "undeposited funds",
                "us-gaap:cashandcashequivalentsatcarryingvalue",
                "us-gaap:cashcashequivalentsrestrictedcashandrestrictedcashequivalents",
            ]),
            ("accounts_receivable", "Accounts Receivable", AccountType::Asset, StatementKind::BalanceSheet, NormalBalance::Debit, None, 1100, &[
                "accounts receivable", "accounts receivable a/r", "ar", "a/r",
                "us-gaap:accountsreceivablenetcurrent",
            ]),
            ("inventory", "Inventory", AccountType::Asset, StatementKind::BalanceSheet, NormalBalance::Debit, None, 1200, &[
                "inventory", "inventory asset", "stock",
                "us-gaap:inventorynet",
            ]),
            ("ppe", "Property, Plant & Equipment", AccountType::Asset, StatementKind::BalanceSheet, NormalBalance::Debit, None, 1300, &[
                "fixed assets", "original cost", "property plant and equipment",
                "ppe", "pp&e",
                "us-gaap:propertyplantandequipmentnet",
            ]),
            ("accumulated_depreciation", "Accumulated Depreciation", AccountType::Asset, StatementKind::BalanceSheet, NormalBalance::Credit, None, 1350, &[
                "accumulated depreciation",
                "us-gaap:accumulateddepreciationdepletionandamortizationpropertyplantandequipment",
            ]),
            ("accounts_payable", "Accounts Payable", AccountType::Liability, StatementKind::BalanceSheet, NormalBalance::Credit, None, 2000, &[
                "accounts payable", "accounts payable a/p", "ap", "a/p",
                "us-gaap:accountspayablecurrent",
            ]),
            ("accrued_expenses", "Accrued Expenses", AccountType::Liability, StatementKind::BalanceSheet, NormalBalance::Credit, None, 2100, &[
                "accrued expenses", "accruals", "accrued liabilities",
                "arizona dept of revenue payable", "board of equalization payable",
                "tax payable", "sales tax payable",
                "us-gaap:accruedliabilitiescurrent",
                "us-gaap:accruedincometaxescurrent",
            ]),
            ("debt", "Debt", AccountType::Liability, StatementKind::BalanceSheet, NormalBalance::Credit, None, 2200, &[
                "loan", "loans", "loan payable", "mastercard", "credit card",
                "notes payable", "debt", "long-term debt",
                "us-gaap:longtermdebtcurrent",
                "us-gaap:longtermdebtnoncurrent",
                "us-gaap:longtermdebtandfinanceleaseobligationscurrent",
                "us-gaap:longtermdebtandfinanceleaseobligationsnoncurrent",
            ]),
            ("equity", "Equity", AccountType::Equity, StatementKind::BalanceSheet, NormalBalance::Credit, None, 3000, &[
                "owners equity", "owner's equity", "opening balance equity",
                "members equity", "stockholders equity",
                "us-gaap:stockholdersequity",
                "us-gaap:stockholdersequityincludingportionattributabletononcontrollinginterest",
            ]),
            ("retained_earnings", "Retained Earnings", AccountType::Equity, StatementKind::BalanceSheet, NormalBalance::Credit, None, 3100, &[
                "retained earnings",
                "us-gaap:retainedearningsaccumulateddeficit",
            ]),
            ("net_income", "Net Income", AccountType::CashFlow, StatementKind::CashFlowStatement, NormalBalance::Credit, Some(CashFlowSection::Operating), 4000, &[
                "net income", "net earnings", "profit",
                "us-gaap:netincomeloss",
            ]),
            ("depreciation_addback", "Depreciation Add-back", AccountType::CashFlow, StatementKind::CashFlowStatement, NormalBalance::Credit, Some(CashFlowSection::Operating), 4100, &[
                "depreciation addback", "depreciation and amortization",
                "us-gaap:depreciationdepletionandamortization",
                "us-gaap:depreciationdepletionandamortizationexpense",
            ]),
            ("working_capital_movement", "Working Capital Movement", AccountType::CashFlow, StatementKind::CashFlowStatement, NormalBalance::Credit, Some(CashFlowSection::Operating), 4200, &[
                "change in working capital",
                "changes in operating assets and liabilities",
                "us-gaap:increasedecreaseinoperatingassetsandliabilitiesnetofacquisitions",
                "us-gaap:netcashprovidedbyusedinoperatingactivities",
            ]),
            ("capex", "Capital Expenditures", AccountType::CashFlow, StatementKind::CashFlowStatement, NormalBalance::Debit, Some(CashFlowSection::Investing), 5000, &[
                "capex", "capital expenditures",
                "purchase of property and equipment",
                "us-gaap:paymentstoacquirepropertyplantandequipment",
            ]),
            ("financing_movement", "Financing Movement", AccountType::CashFlow, StatementKind::CashFlowStatement, NormalBalance::Credit, Some(CashFlowSection::Financing), 6000, &[
                "financing activities", "debt proceeds", "debt repayment",
                "us-gaap:proceedsfromissuanceofdebt",
                "us-gaap:proceedsfromissuanceoflongtermdebt",
                "us-gaap:repaymentsofdebt",
            ]),
        ];

        for (id, name, account_type, statement, normal_balance, cf_section, sort_order, aliases) in specs {
            self.add(StandardAccount {
                id: id.to_string(),
                name: name.to_string(),
                account_type: account_type.clone(),
                statement: statement.clone(),
                normal_balance: normal_balance.clone(),
                cash_flow_section: cf_section.clone(),
                sort_order: *sort_order,
                aliases: aliases.iter().map(|s| s.to_string()).collect(),
            });
        }
    }
}

pub static CHART: LazyLock<StandardChartOfAccounts> =
    LazyLock::new(StandardChartOfAccounts::new);
