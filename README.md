# waccy

Financial Modeling tools in Python

## Features

- Time Value of Money (TVM) calculations
- Discounted Cash Flow (DCF) valuation
- Capital Asset Pricing Model (CAPM)
- Portfolio optimization using Modern Portfolio Theory (MPT)
- Risk analysis and Monte Carlo simulations
- Bond pricing and yield calculations
- Option pricing models (Black-Scholes, Binomial)
- Financial ratios and metrics
- Sensitivity analysis and scenario modeling
- Data visualization and charting

## Three Sheet Model

The Three Sheet Model is a fundamental financial modeling tool that consists of three main components:

1. Income Statement: This sheet focuses on the company's revenues, expenses, and profitability over a specified period.
2. Balance Sheet: The balance sheet provides a snapshot of the company's assets, liabilities, and equity at a particular point in time.
3. Cash Flow Statement: This sheet tracks the inflows and outflows of cash, categorizing them into operating, investing, and financing activities.

The `waccy` package provides a `ThreeSheetModel` class that allows you to create and manipulate a three sheet model easily. It includes methods for inputting data, calculating financial ratios, and generating visualizations.

## Forecasts based on Non-Financial Information

In addition to traditional financial data, `waccy` enables you to incorporate non-financial information into your forecasts. This can include factors such as:

- Industry trends
- Market share and competitive landscape
- Technological advancements
- Regulatory changes
- Macroeconomic indicators

By considering these non-financial aspects, you can create more comprehensive and accurate forecasts. The `Forecast` class in `waccy` provides methods for integrating non-financial data into your financial models.

## Data Sources

### EDGAR

`waccy` includes functionality to retrieve financial data from the Electronic Data Gathering, Analysis, and Retrieval (EDGAR) system, which is maintained by the U.S. Securities and Exchange Commission (SEC). You can access company filings, such as 10-K and 10-Q reports, to extract relevant financial information.

The `EdgarDataSource` class allows you to search for and download specific company filings programmatically.

### QBO and other Accounting Software

`waccy` provides integrations with popular accounting software, such as QuickBooks Online (QBO), to import financial data directly into your models. This streamlines the data collection process and ensures accuracy.

The `QBODataSource` class enables you to authenticate and retrieve data from your QBO account, while the `AccountingDataSource` class serves as a generic interface for integrating with other accounting software.

## How to Contribute

We welcome contributions from the community to enhance and expand the capabilities of `waccy`. To contribute, please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bug fix.
3. Make your changes and ensure that the code follows the project's coding style and guidelines.
4. Write tests to cover your changes and ensure that existing tests pass.
5. Update the documentation, including the README.md and any relevant API references.
6. Submit a pull request describing your changes and referencing any related issues.

Please note that by contributing to `waccy`, you agree to license your contributions under the [MIT License](LICENSE).

If you have any questions or need further assistance, feel free to open an issue on the GitHub repository.

---

We appreciate your interest in contributing to `waccy` and look forward to collaborating with you to make financial modeling in Python more accessible and powerful!
