from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.database import get_session
from app.schemas import ProviderOut, AskRequest, AskResponse
from app.utils.geo import zip_to_latlon, haversine_km
from app.crud import providers_by_drg
from app.nlp import parse_question_llm
import asyncio

router = APIRouter()

@router.get("/providers", response_model=List[ProviderOut], tags=["providers"])
async def get_providers(
    drg: Optional[str] = Query(None),
    zip: Optional[str] = Query(None),
    radius_km: Optional[float] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("average_covered_charges"),
    order: str = Query("asc"),
    session: AsyncSession = Depends(get_session),
):
    drg_code = None
    drg_text = None
    if drg:
        try:
            drg_code = int(drg)
        except ValueError:
            drg_text = drg
    base = await providers_by_drg(session, drg_code, drg_text)
    center = None
    if zip:
        center = zip_to_latlon(zip)
    out = []
    for r in base:
        d = dict(r)
        d["distance_km"] = None
        if center and r["provider_zip_code"]:
            p = zip_to_latlon(r["provider_zip_code"])
            if p:
                d["distance_km"] = haversine_km(center[0], center[1], p[0], p[1])
        out.append(d)
    if center and radius_km:
        out = [x for x in out if x["distance_km"] is not None and x["distance_km"] <= radius_km]
    key = sort_by
    reverse = order == "desc"
    if key == "rating":
        key = "rating_avg"
    if key not in out[0] if out else ["average_covered_charges"]:
        key = "average_covered_charges"
    out.sort(key=lambda x: (float("inf") if x[key] is None else x[key]), reverse=reverse)
    out = out[offset:offset+limit]
    return out

@router.post("/ask", response_model=AskResponse, tags=["assistant"])
async def post_ask(payload: AskRequest, session: AsyncSession = Depends(get_session)):
    parsed = await parse_question_llm(payload.question)
    drg_code = parsed.get("drg_code")
    drg_text = parsed.get("drg_text")
    zip_code = parsed.get("zip")
    radius_km = parsed.get("radius_km", 40.0)
    if not drg_code and not drg_text:
        return AskResponse(answer="Provide a DRG code or description.")
    if not zip_code:
        return AskResponse(answer="Provide a valid ZIP code.")
    base = await providers_by_drg(session, drg_code, drg_text)
    center = zip_to_latlon(zip_code)
    if not center:
        return AskResponse(answer="ZIP not found.")
    enriched = []
    for r in base:
        d = dict(r)
        d["distance_km"] = None
        if r["provider_zip_code"]:
            p = zip_to_latlon(r["provider_zip_code"])
            if p:
                d["distance_km"] = haversine_km(center[0], center[1], p[0], p[1])
        enriched.append(d)
    enriched = [x for x in enriched if x["distance_km"] is not None and x["distance_km"] <= radius_km]
    async def cheapest():
        y = sorted(enriched, key=lambda x: (float("inf") if x["average_covered_charges"] is None else x["average_covered_charges"]))
        return y[:5]
    async def best():
        y = sorted(enriched, key=lambda x: (-1 if x["rating_avg"] is None else x["rating_avg"]), reverse=True)
        return y[:5]
    cheapest_task = cheapest()
    best_task = best()
    cheap, top = await asyncio.gather(cheapest_task, best_task)
    intent = parsed.get("intent", "cost")
    if intent == "quality" and top:
        t = top[0]
        a = f"Top rating near {zip_code}: {t['provider_name']} ({round(t['rating_avg'],1) if t['rating_avg'] is not None else 'N/A'}/10) for DRG {drg_code or drg_text}."
        return AskResponse(answer=a, data=top)
    if cheap:
        c = cheap[0]
        a = f"Cheapest near {zip_code}: {c['provider_name']} with estimated covered charges {c['average_covered_charges']} for DRG {drg_code or drg_text}."
        return AskResponse(answer=a, data=cheap)
    return AskResponse(answer="No results found.")
