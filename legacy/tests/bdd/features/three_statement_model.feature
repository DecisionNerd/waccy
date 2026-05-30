@bdd @outcome
Feature: v0.1.0 three-sheet financial model
  WACCY turns source-specific financial records into a validated workbook-ready model.

  Scenario: QBO fixture produces three validated statements
    Given a balanced QBO financial fixture
    When I build the v0.1.0 workbook model
    Then the workbook has exactly the three expected statements
    And the 2024 income statement reports net income of 316
    And the 2024 balance sheet balance check is zero
    And the 2024 cash flow tie-out is zero
    And the model has no error-level validation issues

  Scenario: EDGAR fixture maps XBRL concepts into the same canonical model
    Given a balanced EDGAR financial fixture
    When I build the v0.1.0 workbook model
    Then the workbook has exactly the three expected statements
    And the 2024 income statement reports revenue of 1200
    And the 2024 balance sheet balance check is zero
    And the 2024 cash flow tie-out is zero
    And the model has no error-level validation issues
