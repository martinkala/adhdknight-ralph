# food-007 — Medication dictionary (2026-10-24)

## Decisions
- `services/food_med_dictionary.py` holds the dictionary (list, upsert + moving entries, soft delete, `stage`
  for adding a missing item without commit). The common input `add_meds` lives in `food_entries.py` next to
  `add_entries` and shares `_append`. `next_position` moved to `food_days.py` so both services can use it
  without a circular import.
- Router `routers/food_meds.py`; `POST /days/{date}/meds` defaults to 201 and switches the response status to 200
  when `needs_classification` is not empty.
- `classify` only answers unknown items; known items always follow the dictionary (changing a kind is the PUT).
- `text_norm` added to the `Entry` response so the web "move" action can call `PUT /med-dictionary/{text_norm}`
  without its own normalization (domain logic stays on the server).
- Web: the classification dialog is part of the `#meds-lists` partial; Django sets `X-Food-Keep-Input` so the
  quick add field gets its text back (same path as `X-Food-Error` in `food_entries.js`).

## Problems / lessons
- htmx 2 fires `htmx:afterRequest` of a form that the swap removed on a surviving ancestor, but it did not
  reach the body handler reliably; `htmx:beforeSwap` (fired on the target before the swap, with
  `detail.requestConfig.elt`) is the dependable hook for "the dialog form succeeded".
- Focus cannot move out of an open modal dialog (the rest of the page is inert): refocus the field in
  `htmx:afterSettle`, after the dialog is gone.
- e2e: `to_have_count` on dialog content passes before `showModal()` runs in `afterSettle`; wait for
  `expect(dialog).to_be_visible()` before measuring boxes.
