# food-003 — Data model and pure domain functions (2026-10-24)

## Decisions
- `app/models/food.py`: abstract `_FoodBase` gives every food table `id` (client-assignable UUID),
  `created_at`, `updated_at` (onupdate) and `deleted_at`. Migration `e5f6a7b8c9d0_add_food_tables`.
- No separate (user_id, date) index on `food_days`; the unique constraint is the index.
- `services/food_constants.py` is the single source of categories, groups, units, med kinds and value ranges.
- `parse_quantity` returns `unit=None` for pieces; zero quantities and `x/0` are not recognized.
- Parser errors are `MeasurementError(ValueError)` with `.code` so routers can map them to API error codes.
- `delete_account` deletes food rows explicitly (children first, before `users`).

## Problems / lessons
- `test_migrations.py` used `downgrade -1` from head to test food-002; with a new head it must downgrade
  to an explicit revision. New migrations should do the same (each test pins its own revision).
- `alembic check` reports pre-existing drift on `invitations.created_at` (model nullable vs. migration);
  not touched here, food tables match the models.
