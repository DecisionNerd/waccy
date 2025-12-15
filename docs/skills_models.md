## Financial modeling skills, methods, and model types

### Model engineering and spreadsheet craft

*Note: Models output to multiple formats, with Google Sheets as the primary spreadsheet platform.*

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

If you tell me the kinds of companies you’re modeling most (SaaS, services, manufacturing, roll-ups, etc.), I can reorganize this into a tighter “core set + industry add-ons” checklist you can standardize across templates.
