# UX Checklist: Scale Color Visualization

**Purpose**: Validate completeness, clarity, and consistency of visual/UX requirements for scale color feedback and numeric display
**Created**: 2026-07-04
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 Does FR-001 specify WHERE the numeric value is displayed within the element card — top, bottom, next to the slider, or as overlay? "Viditeľne v karte elementu" leaves placement unspecified for implementers. [Completeness, Spec §FR-001]
- [ ] CHK002 Are color intensity requirements defined for ALL discrete values in a given range, not just the extremes? FR-002 defines -2, -1, 0, 1, 2 implicitly through acceptance scenarios — but is this coverage explicitly required for arbitrary range sizes (e.g., -5..5)? [Completeness, Spec §FR-002]
- [ ] CHK003 Does the spec define what "predvolený neutrálny štýl" (default neutral style) means for an inactive element card (US1/AS6)? Is it truly neutral (no color) or the original impact-based tint from feature 013? [Completeness, Spec §US1/AS6, §FR-004]
- [ ] CHK004 Are requirements defined for what happens visually immediately after an element is toggled ON from binary=false to binary=true — does color appear at the current slider value, or at the midpoint? [Gap, Coverage]
- [ ] CHK005 Does FR-006 define what the "existing behavior" of `overall_feeling` IS, so implementers know precisely what to preserve? Without a baseline description, "MUST zostať nezmenený" is unverifiable. [Completeness, Spec §FR-006]

## Requirement Clarity

- [ ] CHK006 Is the color intensity mapping in FR-002 confirmed as a linear function? This is stated only in Assumptions ("Intenzita farby je lineárna funkcia hodnoty"), not in the functional requirement itself — can it be missed? [Clarity, Traceability, Spec §FR-002, §Assumptions]
- [ ] CHK007 Does FR-003 specify how saturation is calculated for a range starting at 0 (e.g., caffeine 0..2)? Is value=0 "minimum saturation" (very pale) or "white/neutral"? The spec implies white=zero only for negative ranges (FR-002), but this is ambiguous for 0..N positive ranges. [Clarity, Spec §FR-003]
- [ ] CHK008 Are number formatting requirements defined for negative values — e.g., is "-2" the required format, or could "−2" (Unicode minus), "+2", or "2" also be acceptable? [Clarity, Spec §FR-001]
- [ ] CHK009 Does US2/AS2 ("bledozelená, slabá sýtosť") unambiguously define what the MINIMUM saturation level is? "Slabá sýtosť" is subjective without a reference point. (Q2: B selected — color quantification not required, so flag only if this creates implementation ambiguity.) [Clarity, Spec §US2/AS2]

## Requirement Consistency

- [ ] CHK010 Do US2/AS4 and FR-005 consistently define the same behavior for binary (no-scale) elements? US2/AS4 says "karta ostáva pri pôvodnom farebnom kódovaní… bez čísla" and FR-005 says "NESMÚ byť ovplyvnené novou farebnou logikou" — do both mean the same thing? Does "pôvodné farebné kódovanie" refer to the feature-013 impact-based tint or something else? [Consistency, Spec §FR-005, §US2/AS4]
- [ ] CHK011 Is the color direction for elements with **negative impact AND negative value** consistent between FR-002 and FR-003? FR-002 maps negative values to red, but for a stress element (negative impact) with a negative range, a low (negative) value means LOW stress — a positive outcome. Does the red color mislead the user in this case? [Consistency, Edge Case, Spec §FR-002, §FR-003, §Edge Cases]
- [ ] CHK012 Are the acceptance scenarios in US1 consistent with FR-002 in their treatment of the slider's inactive state? US1/AS6 uses "binary = false" as the trigger, but FR-004 says color is active when "binary = true A scale viditeľný" — is these the same condition, or can the scale be visible while binary = false? [Consistency, Spec §US1/AS6, §FR-004]

## Edge Case Coverage

- [ ] CHK013 Does the spec define requirements for asymmetric ranges (e.g., -1..3 where negative extent ≠ positive extent)? FR-002's "proportional to distance from zero" must behave consistently when max negative magnitude ≠ max positive magnitude. [Edge Case, Spec §FR-002]
- [ ] CHK014 Are requirements defined for a degenerate range where scaleMin == scaleMax? [Edge Case, Gap]
- [ ] CHK015 Does the spec address dark-mode / system theme behavior? Material 3 color tokens behave differently in dark mode — are requirements for dark theme either defined or explicitly excluded? [Non-Functional, Gap]

## Acceptance Criteria Quality

- [ ] CHK016 Is SC-002 ("min. 2 odlišné odtiene pre záporné a 2 pre kladné") objectively measurable without color quantification? Can this criterion be verified during a PR review without specific alpha/saturation values? [Measurability, Spec §SC-002]
- [ ] CHK017 Does SC-001 ("0 extra krokov") capture the full intent of FR-001 — is it sufficient to see the number, or must it be readable at a glance (font size, contrast, overflow handling)? [Measurability, Spec §SC-001]
