from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Provider, DrgPrice, Rating

async def providers_by_drg(session: AsyncSession, drg_code: Optional[int], drg_text: Optional[str]):
    q = (
        select(
            Provider.provider_id,
            Provider.provider_name,
            Provider.provider_city,
            Provider.provider_state,
            Provider.provider_zip_code,
            DrgPrice.ms_drg_definition,
            DrgPrice.ms_drg_code,
            DrgPrice.total_discharges,
            DrgPrice.average_covered_charges,
            DrgPrice.average_total_payments,
            DrgPrice.average_medicare_payments,
            func.avg(Rating.rating).label("rating_avg")
        )
        .join(DrgPrice, DrgPrice.provider_id == Provider.provider_id)
        .join(Rating, Rating.provider_id == Provider.provider_id, isouter=True)
        .group_by(
            Provider.provider_id,
            Provider.provider_name,
            Provider.provider_city,
            Provider.provider_state,
            Provider.provider_zip_code,
            DrgPrice.ms_drg_definition,
            DrgPrice.ms_drg_code,
            DrgPrice.total_discharges,
            DrgPrice.average_covered_charges,
            DrgPrice.average_total_payments,
            DrgPrice.average_medicare_payments
        )
    )
    if drg_code is not None:
        q = q.where(DrgPrice.ms_drg_code == drg_code)
    elif drg_text:
        like = f"%{drg_text}%"
        q = q.where(DrgPrice.ms_drg_definition.ilike(like))
    r = await session.execute(q)
    rows = r.all()
    out = []
    for row in rows:
        out.append({
            "provider_id": row.provider_id,
            "provider_name": row.provider_name,
            "provider_city": row.provider_city,
            "provider_state": row.provider_state,
            "provider_zip_code": row.provider_zip_code,
            "ms_drg_definition": row.ms_drg_definition,
            "ms_drg_code": row.ms_drg_code,
            "total_discharges": int(row.total_discharges) if row.total_discharges is not None else None,
            "average_covered_charges": float(row.average_covered_charges) if row.average_covered_charges is not None else None,
            "average_total_payments": float(row.average_total_payments) if row.average_total_payments is not None else None,
            "average_medicare_payments": float(row.average_medicare_payments) if row.average_medicare_payments is not None else None,
            "rating_avg": float(row.rating_avg) if row.rating_avg is not None else None
        })
    return out
