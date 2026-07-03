from fastapi import APIRouter, HTTPException
from app.schemas.compute import (
    ComputeDailyRequest, ComputeDailyResponse, DetailItem,
    ComputeRangeRequest, ComputeRangeResponse, RangeResult, RangeSummary,
)
from app.services.index_calculator import compute_daily

router = APIRouter(prefix="/api/v1/compute", tags=["Compute"])

ANDROID_INTEGRATION = {
    "schema_version": "1.0",
    "description": "Analysis of Android app computation points and server communication strategy",
    "computation_points": [
        {
            "location": "TrackerViewModel.saveCurrent()",
            "frequency": "on every toggle/slider change",
            "server_candidate": False,
            "reason": "Too frequent, must work offline",
        },
        {
            "location": "HomeViewModel weekly index",
            "frequency": "once on Home screen open",
            "server_candidate": True,
            "reason": "Acceptable latency, not real-time critical",
        },
        {
            "location": "TrackerRepository.evaluateAndAdaptWeights()",
            "frequency": "once per week",
            "server_candidate": True,
            "reason": "Ideal for server — requires 15-day history",
        },
        {
            "location": "NotificationWorker",
            "frequency": "once per night",
            "server_candidate": False,
            "reason": "Must be offline-capable",
        },
    ],
    "recommended_strategy": "update-only",
    "strategy_analysis": {
        "update_only": {
            "description": "Sync to server async after each saveCurrent via WorkManager",
            "pros": ["fewer requests", "works offline", "battery efficient"],
            "cons": ["server data may lag by offline duration"],
        },
        "on_display": {
            "description": "Fetch from server on every Home/Vector screen open",
            "pros": ["always fresh server data"],
            "cons": ["request on every open", "battery drain", "fails offline"],
        },
    },
}


@router.post("/daily", response_model=ComputeDailyResponse)
async def compute_daily_endpoint(request: ComputeDailyRequest):
    config_dict = {k: v.model_dump() for k, v in request.entity_config.items()}
    values_list = [v.model_dump() for v in request.values]

    result = compute_daily(values_list, config_dict, request.active_keys)

    if result is None:
        return ComputeDailyResponse(
            date=request.date,
            index_value=None,
            detail=[],
            active_weight_sum=0.0,
            skipped_keys=list(request.entity_config.keys()),
        )

    return ComputeDailyResponse(
        date=request.date,
        index_value=result.index_value,
        detail=[DetailItem(**d.__dict__) for d in result.detail],
        active_weight_sum=result.active_weight_sum,
        skipped_keys=result.skipped_keys,
    )


@router.post("/range", response_model=ComputeRangeResponse)
async def compute_range_endpoint(request: ComputeRangeRequest):
    config_dict = {k: v.model_dump() for k, v in request.entity_config.items()}
    results: list[RangeResult] = []

    for day in request.days:
        if not day.values:
            results.append(RangeResult(date=day.date, index_value=None, status="no_data"))
            continue

        values_list = [v.model_dump() for v in day.values]
        result = compute_daily(values_list, config_dict, day.active_keys)

        if result is None:
            results.append(RangeResult(date=day.date, index_value=None, status="no_data"))
        elif len([v for v in day.values if v.value_binary == 1 or v.value_scale is not None]) < 3:
            results.append(RangeResult(date=day.date, index_value=result.index_value, status="partial"))
        else:
            results.append(RangeResult(date=day.date, index_value=result.index_value, status="computed"))

    computed = [r for r in results if r.index_value is not None]
    avg = round(sum(r.index_value for r in computed) / len(computed), 2) if computed else None

    return ComputeRangeResponse(
        results=results,
        summary=RangeSummary(
            days_requested=len(results),
            days_computed=len(computed),
            days_no_data=sum(1 for r in results if r.status == "no_data"),
            average_index=avg,
        ),
    )


@router.get("/android-integration")
async def android_integration():
    return ANDROID_INTEGRATION
