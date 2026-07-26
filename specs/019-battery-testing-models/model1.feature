# Source draft: specs/019-battery-testing-models/model1.txt
# Entity keys / weights / scales reference: android_app/app/src/main/assets/entities.yaml
# Algorithm reference: android_app IndexCalculator.computeDailyIndexGrouped()
#                       server/app/services/index_calculator.py compute_daily()
#
# This file is descriptive only for now (no step definitions yet). It is meant to become
# the shared spec that both the Android instrumentation tests and the Python server BDD
# suite (server/tests/bdd/) implement steps against, so the two engines can be verified
# against the exact same scenarios.
#
# Scenario/case numbers (001, 002, ...) mirror the "Case N" numbering used in model1.txt,
# zero-padded to 3 digits so the set sorts and extends cleanly (e.g. Case 10 -> 010).
#
# KNOWN GAP — read before wiring up steps:
# server/app/services/index_calculator.py normalizes every scale value as (value - 1) / 4,
# i.e. it assumes every element uses a fixed 1..5 scale (see the "e=(4-1)/4=..." comments in
# server/tests/bdd/fixtures/1_day.yaml). The Android IndexCalculator instead normalizes each
# element using its own scale_min/scale_max from entities.yaml. Almost every element in the
# current entities.yaml uses a scale other than 1..5 (most are 1..3, some -2..2), so the two
# engines will NOT agree on the scenarios below until compute_daily() is updated to use
# per-element scale bounds. The percentages in this file are computed the Android way.

Feature: Battery charge across representative category/value combinations
  As a developer of the ADHD tracker
  I want a shared set of scenarios describing what the battery percentage should be
  for representative combinations of daily values
  So that Android instrumentation tests and Python server tests can both be driven
  from the same specification

  Background:
    Given the entity weight configuration from "entities.yaml"

  @model1 @case001
  Scenario: Case 001 - Base trackable roots at their lowest value, no subcategories recorded
    # "Zakladne kategorie - values 1 - no childs". The draft records a value for every root
    # category (Strava/Structure/Pracovne techniky/Lifestyle/Head), so all of them are listed
    # below for fidelity to the source model — but food/structure/working_techniques/
    # lifestyle/head are category headers (impact is unset), not trackable elements
    # themselves. Per the current C1 algorithm a category only contributes once one of its
    # children is recorded; with no children recorded here, their rows below are inert and
    # only the four standalone trackable roots actually count towards the result.
    Given the following daily values are recorded:
      | element            | value |
      | overall_feeling    | 1     |
      | sleep              | 1     |
      | physical_activity  | 1     |
      | food               | 1     |
      | structure          | 1     |
      | working_techniques | 1     |
      | lifestyle          | 1     |
      | head               | 1     |
      | mindfulness        | 1     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the index value is approximately 37.5 with tolerance 0.1

  @model1 @case002
  Scenario: Case 002 - Base trackable roots at their maximum value, no subcategories recorded
    # "Zakladne kategorie - values max". Same "no childs" / inert-category-row reasoning as
    # Case 001. The draft also lists "Pracovne techniky 1" (not "max") among these values;
    # kept as-is below since working_techniques has no active children here either way, so
    # that row has no effect on the result regardless of its value.
    Given the following daily values are recorded:
      | element            | value |
      | overall_feeling    | 2     |
      | sleep              | 2     |
      | physical_activity  | 3     |
      | food               | 2     |
      | structure          | 2     |
      | working_techniques | 1     |
      | lifestyle          | 2     |
      | head               | 2     |
      | mindfulness        | 2     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the index value is approximately 91.25 with tolerance 0.1

  @model1 @case003
  Scenario: Case 003 - No values recorded for the day
    # "Zakladne kategorie - ziadny zaznam". The draft noted "Baterka 0%", but a day with
    # zero recorded values never gets an index computed at all — Android's
    # computeAndSaveDailyIndex() returns early on empty values and HomeScreen shows "—",
    # not "0%". A literal 0% would mean "the worst possible day was recorded", which is a
    # different fact from "no day was recorded" — the two must stay visually distinct.
    Given no values are recorded for the day
    When the daily battery index is computed
    Then the result is null without error
    And the battery indicator shows the "no data" placeholder instead of "0%"

  @model1 @case010
  Scenario: Case 010 - All positive-impact subcategories recorded, negative ones left untouched
    # "Zakladne kategorie + all positive childs, no negative childs". Every positive-impact
    # child across food/structure/working_techniques/head is recorded at value 1; negative
    # children (caffeine, alcohol, Procrastination, stress_work, stress_personal, Adiction)
    # are NOT recorded. lifestyle has only negative children, so with none active it is
    # skipped entirely — same rule that makes the empty categories in Case 001/002 inert.
    #
    # CAVEAT — flagging, not resolving: most of these children use a scale of [1, 2, 3],
    # where 1 is the scale's minimum, so recording "1" normalizes to 0.0 (the worst point
    # on that scale), not "did the habit". That is why this scenario's index (~21.76) comes
    # out lower than Case 001 (37.5) despite recording far more positive activity. This is
    # likely a product decision to make: either these habit scales should start above their
    # "not done" value, or "1" here needs to mean something else than "minimum".
    Given the following daily values are recorded:
      | element            | value |
      | overall_feeling    | 1     |
      | sleep              | 1     |
      | physical_activity  | 1     |
      | mindfulness        | 1     |
      | nutrition_protein  | 1     |
      | vitamins           | 1     |
      | externalisation    | 1     |
      | time_blocking      | 1     |
      | body_doubling      | 1     |
      | routine            | 1     |
      | physical_notes     | 1     |
      | pomodoro           | 1     |
      | just2minutes       | 1     |
      | eatthefrog         | 1     |
      | timeboxing         | 1     |
      | dedicated_place    | 1     |
      | nodisruption       | 1     |
      | book               | 1     |
      | learn              | 1     |
      | socialisation      | 1     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the index value is approximately 21.76 with tolerance 0.1

  @model1 @case011
  Scenario: Case 011 - Every category and subcategory recorded at its maximum scale value
    # New case, requested alongside Case 001: unlike Case 010, this records literally every
    # node that has a scale — every root category AND every subcategory, including the
    # negative-impact ones (caffeine, alcohol, Procrastination, stress_work,
    # stress_personal, Adiction) — each at the top of its own scale.
    #
    # NOTE: lifestyle and head have no "scale" defined on the category node itself in
    # entities.yaml (unlike food/structure/working_techniques), so they have no row here;
    # their children are still fully recorded below.
    #
    # RESULT CAVEAT: this does NOT reach 100%. For a negative-impact element, its scale
    # maximum is its worst real-world state (most alcohol, most stress, most addiction), so
    # recording every element at its literal maximum simultaneously maximizes the "good"
    # elements and minimizes the "bad" ones' contribution. Concretely: lifestyle's group
    # average drops to 0.0 (both children are negative and maxed out) and head's group
    # average drops to ~0.167 (Adiction's weight of 15 dwarfs its 3 positive siblings'
    # combined weight of 3, and Adiction is inverted to 0.0). "Everything at max" is
    # therefore not the same scenario as "the best possible day" — that would require
    # negative-impact elements at their scale *minimum* instead.
    Given the following daily values are recorded:
      | element            | value |
      | overall_feeling    | 2     |
      | sleep              | 2     |
      | physical_activity  | 3     |
      | food               | 2     |
      | caffeine           | 3     |
      | alcohol            | 3     |
      | nutrition_protein  | 2     |
      | vitamins           | 3     |
      | structure          | 3     |
      | externalisation    | 3     |
      | time_blocking      | 3     |
      | body_doubling      | 3     |
      | routine            | 3     |
      | physical_notes     | 3     |
      | Procrastination    | 3     |
      | working_techniques | 3     |
      | pomodoro           | 3     |
      | just2minutes       | 3     |
      | eatthefrog         | 3     |
      | timeboxing         | 3     |
      | dedicated_place    | 3     |
      | nodisruption       | 3     |
      | stress_work        | 3     |
      | stress_personal    | 3     |
      | book               | 3     |
      | learn              | 3     |
      | socialisation      | 3     |
      | Adiction           | 3     |
      | mindfulness        | 3     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the index value is approximately 77.21 with tolerance 0.1

  @model1 @case012
  Scenario: Case 012 - Only positive-impact elements recorded, all at their maximum
    # Follow-up to Case 011: instead of recording every node, this records ONLY elements
    # with impact +1 (the standalone trackable roots plus every positive-impact
    # subcategory), each at the top of its own scale. Negative-impact elements (caffeine,
    # alcohol, Procrastination, stress_work, stress_personal, Adiction) are not recorded at
    # all. Category headers (food/structure/working_techniques/lifestyle/head) are not
    # recorded either — they have no impact of their own, so they aren't "positive" or
    # "negative", they just pick up whichever of their children are active.
    #
    # RESULT: lifestyle has no positive-impact children at all, so with nothing recorded
    # for it, it is skipped entirely (same "no active children" rule as Case 001/002/010).
    # Every other category ends up with 100% of its active children maxed out, so the
    # index reaches a clean 100%.
    Given the following daily values are recorded:
      | element           | value |
      | overall_feeling   | 2     |
      | sleep             | 2     |
      | physical_activity | 3     |
      | nutrition_protein | 2     |
      | vitamins          | 3     |
      | externalisation   | 3     |
      | time_blocking     | 3     |
      | body_doubling     | 3     |
      | routine           | 3     |
      | physical_notes    | 3     |
      | pomodoro          | 3     |
      | just2minutes      | 3     |
      | eatthefrog        | 3     |
      | timeboxing        | 3     |
      | dedicated_place   | 3     |
      | nodisruption      | 3     |
      | book              | 3     |
      | learn             | 3     |
      | socialisation     | 3     |
      | mindfulness       | 3     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the index value is approximately 100.0 with tolerance 0.01

  @model1 @case013
  Scenario: Case 013 - Only negative-impact elements recorded, all at their maximum
    # The mirror image of Case 012: ONLY elements with impact -1 are recorded (caffeine,
    # alcohol, Procrastination, stress_work, stress_personal, Adiction), each at the top of
    # its own scale — i.e. their worst real-world state. No positive-impact elements and no
    # standalone trackable roots (overall_feeling, sleep, physical_activity, mindfulness)
    # are recorded at all.
    #
    # RESULT: overall_feeling/sleep/physical_activity/mindfulness and working_techniques are
    # skipped entirely (no active children and not recorded directly). Every category that
    # does have an active child (food, structure, lifestyle, head) ends up with all of its
    # active children inverted to 0.0, so the index bottoms out at a clean 0%.
    Given the following daily values are recorded:
      | element         | value |
      | caffeine        | 3     |
      | alcohol         | 3     |
      | Procrastination | 3     |
      | stress_work     | 3     |
      | stress_personal | 3     |
      | Adiction        | 3     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the index value is approximately 0.0 with tolerance 0.01

  @model1 @case100 @needs-clarification
  Scenario: Case 100 - Negative-impact elements mixed with positive ones
    # "zarad negativne values" — exploratory scenario from the draft; no expected battery
    # value was specified yet, and it stays open here too.
    # NOTE: the draft's "Kofein -1" is outside caffeine's configured scale ([1, 2, 3] in
    # entities.yaml) — needs a decision before this can become a concrete assertion.
    Given the following daily values are recorded:
      | element            | value |
      | sleep              | -1    |
      | physical_activity  | 2     |
      | caffeine           | -1    |
      | nutrition_protein  | 1     |
      | vitamins           | 1     |
      | mindfulness        | 1     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the expected index value is not yet defined pending the caffeine scale clarification

  @model1 @case101 @needs-clarification
  Scenario: Case 101 - Sleep below baseline offset by other positive values
    # Draft "Case 101" — exploratory, no expected battery value specified yet.
    Given the following daily values are recorded:
      | element            | value |
      | overall_feeling    | 1     |
      | sleep              | -1    |
      | physical_activity  | 1     |
      | nutrition_protein  | 1     |
      | stress_personal    | 1     |
    And no other elements are recorded
    When the daily battery index is computed
    Then the expected index value is not yet defined pending review
