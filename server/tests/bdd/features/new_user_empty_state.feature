Feature: Empty State Handling
  As a developer
  I want to verify the server handles new users and empty data gracefully
  So that the API never crashes on missing or partial input

  Scenario: Empty values list returns null index without error
    Given no values are provided
    When I compute the daily index
    Then the result is null without error

  Scenario: No active keys returns null index
    Given values exist but no active keys are specified
    When I compute the daily index
    Then the result is null without error

  Scenario: Partial day with one element returns partial status
    Given one element is filled out of three active
    When I compute the daily index
    Then the index value is not null
    And the index is between 0 and 100

  Scenario: 3-day range with all empty days
    Given a 3-day range with no values on any day
    When I compute the range
    Then all results have status "no_data"
    And all index values are null
