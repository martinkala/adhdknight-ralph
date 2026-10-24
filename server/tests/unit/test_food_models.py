"""food-003 FR-1: food tables exist in the test schema and enforce their constraints."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.food import FoodBloodPressure, FoodDay, FoodEntry, FoodMedDictionary, FoodWeight
from app.models.user import User


async def _user(db) -> User:
    user = User(email=f"food-model-{uuid.uuid4().hex[:8]}@example.com", password_hash="x")
    db.add(user)
    await db.flush()
    return user


async def test_food_rows_roundtrip_with_defaults(db_session):
    user = await _user(db_session)
    day = FoodDay(user_id=user.id, date="2026-10-24", sleep_quality=3)
    db_session.add(day)
    await db_session.flush()
    db_session.add_all([
        FoodEntry(day_id=day.id, user_id=user.id, category="breakfast", text="Ryža",
                  text_norm="ryza", quantity=Decimal("0.5"), unit="kg", position=0),
        FoodWeight(day_id=day.id, user_id=user.id, kg=Decimal("80.6"), measured_at="07:30"),
        FoodBloodPressure(day_id=day.id, user_id=user.id, systolic=130, diastolic=85, pulse=72),
        FoodMedDictionary(user_id=user.id, text_norm="emanera", display_text="Emanera", kind="medication"),
    ])
    await db_session.flush()

    assert len(day.id) == 36 and day.created_at is not None and day.updated_at is not None
    assert day.deleted_at is None


async def test_client_supplied_id_is_kept(db_session):
    user = await _user(db_session)
    client_id = str(uuid.uuid4())
    day = FoodDay(id=client_id, user_id=user.id, date="2026-10-20")
    db_session.add(day)
    await db_session.flush()
    assert day.id == client_id


async def test_day_unique_per_user_and_date(db_session):
    user = await _user(db_session)
    db_session.add(FoodDay(user_id=user.id, date="2026-10-24"))
    await db_session.flush()
    db_session.add(FoodDay(user_id=user.id, date="2026-10-24"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_same_date_for_different_users_is_allowed(db_session):
    a, b = await _user(db_session), await _user(db_session)
    db_session.add_all([FoodDay(user_id=a.id, date="2026-10-24"), FoodDay(user_id=b.id, date="2026-10-24")])
    await db_session.flush()


async def test_med_dictionary_unique_per_user_and_text_norm(db_session):
    user = await _user(db_session)
    db_session.add(FoodMedDictionary(user_id=user.id, text_norm="emanera", display_text="Emanera", kind="medication"))
    await db_session.flush()
    db_session.add(FoodMedDictionary(user_id=user.id, text_norm="emanera", display_text="emanera", kind="supplement"))
    with pytest.raises(IntegrityError):
        await db_session.flush()
