Feature: ADHD Index Calculation
  As a developer
  I want to verify the server computes the ADHD index identically to the Android app
  So that regression testing can be done without the mobile device

  Scenario: Single day with scale elements
    Given the fixture "1_day"
    When I compute the daily index for day "2026-06-30"
    Then the index value is approximately 86.61 with tolerance 0.02

  Scenario: All elements at maximum values produces index 100
    Given a single day with all elements at maximum
    When I compute the daily index
    Then the index value is approximately 100.0 with tolerance 0.01

  Scenario: All elements at minimum values produces index 0
    Given a single day with all elements at minimum
    When I compute the daily index
    Then the index value is approximately 0.0 with tolerance 0.01

  Scenario: Negative impact element is inverted
    Given a single element "stress_work" with impact -1 and binary value 1
    When I compute the daily index
    Then the index value is approximately 0.0 with tolerance 0.01

  Scenario: Group node with subnodes uses C1 algorithm
    Given a group node "lifestyle" with weight 20.0 and two active children both done
    When I compute the daily index
    Then the index value is approximately 100.0 with tolerance 0.01

  Scenario: Group node with one of two subnodes done gives 50 percent
    Given a group node "lifestyle" with weight 20.0 and one of two children done
    When I compute the daily index
    Then the index value is approximately 50.0 with tolerance 0.01

  Scenario: Parent weight stays constant regardless of child count
    Given a parent node with 1 child all done
    And a parent node with 3 children all done
    When I compute both configurations
    Then both produce the same index value
