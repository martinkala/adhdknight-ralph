# Tests Checklist: Scale Color Visualization

**Purpose**: Validate completeness, clarity, and measurability of test specification requirements for negative range edge cases and ASRS compatibility
**Created**: 2026-07-04
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 Does FR-007 enumerate the required test matrix — which specific (impact, scaleMin, scaleMax, value) combinations must be tested? "Všetky kombinácie dopadov" is broad; without a defined matrix, coverage gaps may go undetected. [Completeness, Spec §FR-007]
- [ ] CHK002 Is the specific edge case "negative impact element + negative value → value_effective = 0" explicitly listed as a required test case in FR-007 or FR-008? It is described in the Edge Cases section but not traceable to a specific test requirement. [Completeness, Spec §Edge Cases, §FR-007]
- [ ] CHK003 Does FR-008 require tests for the weight adaptation algorithm (Constitution Principle II) when all elements have negative-range values? Correlation of a negative-range element with `overall_feeling` drives adaptive weights — is this tested? [Completeness, Gap, Spec §FR-008]
- [ ] CHK004 Are regression tests for backward compatibility of `valueEffective(valueBinary, valueScale)` with the original 1-5 default range explicitly required? Feature 013 changed the signature — are the pre-013 cases part of the required test coverage? [Completeness, Gap]
- [ ] CHK005 Does the spec require tests for the ASRS re-calibration threshold (`|ASRS - priemer_indexu_14d| > 10`) when index values are computed from a mix of negative-range and positive-range elements? [Completeness, Gap, Spec §US3]

## Requirement Clarity

- [ ] CHK006 Does FR-008 define what "minimum" means for each element — is it the element's own `scaleMin`, the globally lowest possible value, or zero? "Všetky elementy na minime" is ambiguous across elements with different ranges. [Clarity, Spec §FR-008]
- [ ] CHK007 Does FR-007 specify whether test coverage must include BOTH unit tests AND integration tests (Room in-memory), or unit tests only? Constitution Principle VI distinguishes these categories. [Clarity, Spec §FR-007]
- [ ] CHK008 Does FR-009 specify WHAT FORM the ASRS compatibility documentation must take — in-code comment, appended section in spec.md, separate research note? Without format, "dokumentácia MUST popisovať" is unverifiable. [Clarity, Spec §FR-009]
- [ ] CHK009 Does FR-009 define the minimum required content of the ASRS compatibility solution — e.g., must it include a concrete code change proposal, or is a risk description sufficient? [Clarity, Spec §FR-009]
- [ ] CHK010 Does US3/AS3 ("výsledok zodpovedá vzorcu z constitution Princíp II") define which formula variant applies — the formula with scaleMin/scaleMax already updated in feature 013, or the original 1-5 formula? [Clarity, Spec §US3/AS3]

## Acceptance Criteria Quality

- [ ] CHK011 Is SC-003 ("100% pass rate for new tests") scoped precisely enough — does it refer to a specific test class (e.g., `IndexCalculatorTest`), all unit tests, or the entire test suite? [Measurability, Spec §SC-003]
- [ ] CHK012 Is SC-004 ("existujúce testy nie sú rozbité") verifiable — is there a baseline test count or a list of specific tests that MUST continue to pass? Without a baseline, regressions are detectable only incidentally. [Measurability, Spec §SC-004]
- [ ] CHK013 Does SC-005 ("dokumentácia ASRS kompatibility … obsahuje konkrétne príklady") define how many examples are required, or what constitutes a "concrete example"? [Measurability, Spec §SC-005]

## Scenario Coverage

- [ ] CHK014 Are requirements defined for the case where `scaleMin == scaleMax` in a test context — does the formula divide by zero? Is this a required boundary test? [Edge Case, Coverage, Spec §FR-007]
- [ ] CHK015 Does the spec require tests for the ASRS weight normalization step when elements have heterogeneous ranges (some 1-5, some -2..2, some 0..2)? The weight sum normalization in Constitution Principle II may behave differently with mixed configurations. [Coverage, Gap]
- [ ] CHK016 Are requirements defined for test data setup — which entities.yaml configuration (or subset) is assumed as the baseline for unit tests? Tests referencing specific elements (sleep, stress_work) depend on configuration. [Assumption, Spec §FR-007]

## Dependencies & Assumptions

- [ ] CHK017 Does the spec document that feature 013's `valueEffective` signature change is a prerequisite for these tests, and that tests must verify both the old and new call signature? [Dependency, Gap]
- [ ] CHK018 Is the assumption that `overall_feeling` always uses scaleMin=1, scaleMax=5 explicitly required as a test invariant in FR-007 or FR-008? Constitution Principle IV mandates this — does the test spec enforce it? [Assumption, Spec §FR-007, §FR-008]
