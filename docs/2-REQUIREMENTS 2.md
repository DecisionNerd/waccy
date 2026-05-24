# WACCY Requirements

This document captures the financial modeling requirements, methods, and deliverables that shape WACCY's roadmap. The v0.1.0 release is intentionally narrower than this full list: it targets QBO/QuickBooks and EDGAR inputs, normalized accounts, a three-statement model, validation checks, and XLSX export.

## v0.1.0 Release Requirements

The first useful release should prove the core modeling loop with a narrow, testable vertical slice:

- load QBO/QuickBooks fixture data
- load EDGAR fixture data
- produce a normalized financial dataset from both sources
- normalize source accounts and concepts into WACCY standard accounts
- validate the mapped financial dataset before model construction
- build a three-statement model object
- export an `.xlsx` workbook with Income Statement, Balance Sheet, and Cash Flow Statement sheets
- report unmapped accounts, missing periods, balance-sheet imbalance, and cash-flow tie-out failures
- include fixture-driven tests for the full path from source data to workbook

Live integrations can be documented behind clear configuration paths, but fixtures are enough to prove the v0.1.0 modeling loop.

## Data Quality Requirements

WACCY must make data quality measurable and reviewable:

- normalized records should preserve source provenance before mapping
- every model line item should trace back to source data
- every source account or concept should map to a canonical WACCY account or appear in diagnostics
- mappings should carry confidence or review status
- validation should catch structurally invalid data before model construction
- reconciliation should catch broken statements after model construction
- users should be able to inspect and override ambiguous classifications

Quality reporting should prioritize actionability over ornamental scores.

## Layer Requirements

The v0.1.0 implementation should establish the reusable layers that future financial models and metrics will depend on:

- **Raw extracted data**: source-shaped records with provenance.
- **Normalized financial dataset**: source-agnostic records with periods, accounts or concepts, amounts, units, source system, and provenance.
- **Mapped financial dataset**: normalized records connected to WACCY standard accounts with confidence and review status.
- **Validated financial dataset**: mapped records plus diagnostics and reconciliation results.
- **Model and metric outputs**: source-agnostic builders that consume validated data.
- **Exports**: rendered workbook or other output formats.

Extractors should not build financial models. Model and metric builders should not depend on source-specific QBO or EDGAR structures.

## Standardization Requirements

All financial data must pass through a standard ontology before it becomes model output. The ontology should support:

- account type and hierarchy
- statement placement
- normal balance/sign convention
- cash-flow classification
- source aliases for QBO account names and EDGAR/XBRL concepts
- industry-specific extension without fragmenting the standard

The ontology is a product requirement, not only an implementation detail: without standardization, WACCY cannot compare companies, quantify mapping quality, or generate reliable downstream models.

## Financial Modeling Skills, Methods, And Model Types

### Model engineering and spreadsheet craft

*Note: v0.1.0 targets XLSX export. Google Sheets support is a longer-term output option.*

* **Model architecture**: modular tabs, inputs/assumptions separation, consistent time axis, sign conventions, hardcode isolation
* **Formatting standards**: color conventions, units (000s/MM), date handling, print-ready layouts
* **Formula design**: robust links, avoiding fragile offsets, transparent logic, minimizing circularity
* **Speed and scale**: efficient formulas, calc settings, iterative calc controls, performance hygiene
* **Auditability**: check rows, balance checks, roll-forwards, flags, reconciliation tables, trace precedents/dependents
* **Scenario tooling**: data tables, scenario toggles, switch cases, goal seek, solver, sensitivity matrices, tornado charts
* **Advanced spreadsheet tools** (optional but common in practice): pivot tables, named ranges, dynamic arrays (ARRAYFORMULA/LAMBDA in Google Sheets), query functions, Apps Script for automation (Google Sheets equivalent of VBA/macros)

### Accounting and financial statement analysis (skills)

* **Income statement mechanics**: revenue recognition basics, COGS vs opex classification, margin stack, SBC, non-recurring items
* **Balance sheet mechanics**: working capital accounts, deferred revenue, accrued expenses, debt vs equity classification, lease accounting awareness
* **Cash flow mechanics**: indirect method, non-cash add-backs, NWC bridge, capex vs opex, financing/investing classification
* **Quality of earnings**: normalization adjustments, run-rate vs reported, one-time costs, restructuring, FX impacts
* **Ratio and returns**: ROIC/ROE/ROA, DuPont, margin/turnover, leverage, coverage, liquidity
* **Credit lens**: leverage ratios, fixed-charge coverage, covenant math, debt capacity framing

### Forecasting methods (drivers, not vibes)

* **Revenue builds**: price × volume, units × ARPU, cohort/retention models (SaaS), pipeline conversion, capacity-based revenue
* **Cost builds**: variable vs fixed cost frameworks, headcount models, gross margin drivers, opex by function, inflation indexing
* **Working capital**: DSO/DIO/DPO, % of revenue, seasonality, inventory turns, deferred revenue dynamics
* **Capex & depreciation**: capex by category, asset lives, depreciation waterfalls, capitalized software
* **Debt & interest**: revolver mechanics, fixed/floating rate modeling, spreads, amortization schedules, cash sweep waterfalls
* **Equity & shares**: basic/diluted share count, treasury stock method, convertibles, RSUs/options, buybacks/issuance
* **Taxes**: effective tax rate vs statutory, deferred taxes (DTAs/DTLs), NOL utilization, interest limitation awareness
* **Segment and geography**: segment KPIs, mix shift, FX translation, margin differences by segment

### Core valuation methods

* **DCF (intrinsic valuation)**

  * Unlevered FCF construction (NOPAT + D&A − Capex − ΔNWC)
  * Discounting mechanics (stub periods, mid-year convention)
  * Terminal value (perpetuity growth, exit multiple)
  * Enterprise → equity bridge (net debt, minority interest, investments, preferred)
  * WACC build (cost of equity, cost of debt, target capital structure)
* **Relative valuation**

  * Trading comps (peer selection, spreading, normalization, EV/Revenue, EV/EBITDA, P/E, sector metrics)
  * Transaction comps (precedent deals, implied multiples, control premiums, deal adjustments)
* **Common “extras”**

  * **Sum-of-the-parts (SOTP)**, **implied multiple triangulation**, **football field outputs**
  * **APV** (Adjusted Present Value) for leverage/tax shield clarity
  * **Residual income / economic profit** frameworks (less common but useful in some cases)

### M&A and pro forma analysis methods

* **Accretion/dilution**: pro forma EPS impact, synergy timing, financing mix sensitivities
* **Sources & uses**: cash/stock/debt mix, fees, refinancing, rollover equity
* **Purchase accounting / PPA**: goodwill, intangibles, step-ups, deferred taxes, amortization impacts
* **Deal structures**: fixed vs floating exchange ratio, collars, contingent consideration/earn-outs (when applicable)
* **Synergy modeling**: cost vs revenue synergies, phasing, one-time integration costs, dis-synergies
* **Contribution analysis**: relative ownership, value transfer, synergy split logic
* **Pro forma statements**: combined IS/BS/CF with transaction adjustments and financing effects

### LBO and private equity modeling methods

* **Returns math**: IRR, MOIC (multiple on invested capital), cash-on-cash
* **Capital structure**: senior/mezz/notes/PIK, revolver, management rollover, preferred equity
* **Debt schedules**: mandatory amortization, cash sweep, refinancing, call protection (high-yield awareness)
* **Interest modeling**: fixed vs floating, SOFR/LIBOR + spread, blended rates, average balance conventions
* **Tax effects**: interest shield, NOLs, limitations awareness, cash tax vs book tax framing
* **Exit analysis**: exit multiple, IPO/strategic/secondary, deleveraging effects, dividend recap modeling
* **Sensitivity grids**: entry/exit multiple, leverage, EBITDA growth, margin, hold period, rate environment

### Data sourcing, standardization, and “spreading”

* **Primary sources**: 10-K/10-Q/8-K, proxy statements, earnings releases, presentations, call transcripts
* **Normalization and adjustments**: GAAP ↔ non-GAAP reconciliation, run-rate adjustments, segment restatements
* **Consistency work**: calendarization, LTM building, pro forma adjustments, currency and FX handling
* **Market data integration**: share price, shares outstanding, debt pricing, yield curves/spreads (as needed)

### Presentation and decision-support outputs

* **Valuation summaries**: ranges, quartiles/medians, implied valuations, key assumptions callouts
* **Charts & tables**: comps tables, sensitivity tables, bridge charts (EV→Eq), debt waterfalls, return bridges
* **Narrative framing**: investment highlights, key risks, diligence questions, KPI dashboards

---

## Common model types (deliverables)

* **3-statement integrated operating model**
* **DCF valuation model**
* **Trading comps model**
* **Transaction comps model**
* **Merger model (accretion/dilution + purchase accounting)**
* **LBO model**
* **SOTP / break-up valuation model**
* **Cap table & dilution model (options/convertibles)**
* **Credit / covenant compliance model**
* **Budget vs actual / forecast (FP&A) model**
* **Project finance / infrastructure model (cash waterfall, DSCR/LLCR)**
* **Real estate (REIT) / property cash flow model**
* **SaaS cohort + unit economics model**
* **Carve-out / spin / restructuring model (when relevant)**

## Phased Roadmap Requirements

### Phase One: Core Foundation And Three-Statement Models

Objective: establish the foundational platform with QBO/QuickBooks and EDGAR fixture-supported extraction, standardized ontology, basic account mapping, model generation, validation, and XLSX export.

Required capabilities:

- core platform architecture with a modular data-source interface
- minimum WACCY chart of accounts for three-statement modeling
- deterministic mapping from QBO accounts and EDGAR/XBRL concepts
- three-statement model generation
- reconciliation checks and quality diagnostics
- fixture-driven tests for both QBO and EDGAR paths

### Phase Two: Public Market Data And Pattern Learning

Objective: use SEC EDGAR as both public-company source data and a corpus of professional classification examples.

Required capabilities:

- richer EDGAR extraction from 10-K, 10-Q, and 8-K filings
- normalization and calendarization of public company periods
- pattern extraction for classification and causal-chain learning
- comparison workflows that help interpret small-business data through better-documented examples

### Phase Three: Advanced Valuation Models

Objective: build valuation and transaction analysis on top of standardized three-statement outputs.

Required capabilities:

- DCF valuation
- trading comparables
- transaction comparables
- M&A and pro forma analysis
- LBO model generation
- sensitivity and scenario tooling

### Phase Four: Specialized Model Types

Objective: extend WACCY into industry and use-case-specific models.

Required capabilities:

- SaaS cohort and unit economics models
- real estate and REIT models
- project finance and infrastructure models
- cap table and dilution analysis
- credit and covenant compliance models
- industry-specific template libraries

### Phase Five: Advanced Analysis And Decision Support

Objective: help users reason across scenarios, risks, and fragmented sources.

Required capabilities:

- multi-scenario model generation
- automated sensitivity analysis
- strategic planning models
- source synthesis from documents and operational systems
- confidence-aware decision-support outputs
