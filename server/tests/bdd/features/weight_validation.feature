Feature: Weight Validation
  As a developer
  I want to verify that weight assignment rules are correct
  So that no element has disproportionate influence based on its child count

  Scenario: 1-element category equals 3-element category when all done
    Given a parent node with 1 child all done
    And a parent node with 3 children all done
    When I compute both configurations
    Then both produce the same index value

  Scenario: Subnode parent weight does not exceed root weight
    Given a group node "lifestyle" with weight 20.0 and two active children both done
    When I compute the daily index
    Then the active weight sum equals 20.0

  Scenario: 15 days fixture loads successfully
    Given the fixture "15_days"
    Then the fixture has 15 days
    And 3 days have no data
