import os
import pandas as pd
import numpy as np
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from pathlib import Path

def to_str_or_none(x):
    if pd.isna(x):
        return None
    return str(x)

def to_int_or_none(x):
    try:
        return None if pd.isna(x) else int(x)
    except Exception:
        return None

def to_float_or_none(x):
    try:
        return None if pd.isna(x) else float(x)
    except Exception:
        return None

def normalize_zip(z):
    s = to_str_or_none(z)
    if s is None:
        return None
    return s.zfill(5)

def parse_drg_code_from_desc(desc):
    if desc is None:
        return None
    s = str(desc)
    for token in s.replace("–","-").split("-"):
        t = token.strip()
        if t.isdigit() and len(t) in (3,4):
            try:
                v = int(t[:3])
                return v
            except Exception:
                pass
    return None

def map_columns(df):
    cols = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None
    c_provider_id = pick("provider_id","rndrng_prvdr_ccn","providerid","prvdr_num")
    c_provider_name = pick("provider_name","rndrng_prvdr_org_nm","providername", "rndrng_prvdr_org_name")
    c_provider_city = pick("provider_city","rndrng_prvdr_city","city")
    c_provider_state = pick("provider_state","rndrng_prvdr_state_abrvtn","state")
    c_provider_zip = pick("provider_zip_code","rndrng_prvdr_zip5","zip_code","zipcode","zip")
    c_drg_desc = pick("ms_drg_definition","drg_desc","drg_definition","drg_def","ms_drg_definition")
    c_drg_code = pick("ms_drg_code","ms_drg_cd","drg_code")
    c_total_discharges = pick("total_discharges","tot_dschrgs")
    c_avg_cov = pick("average_covered_charges","avg_cvrd_chrg","avgcoveredcharges", "avg_submtd_cvrd_chrg")
    c_avg_total = pick("average_total_payments","avg_tot_pymt_amt","avgtotalpayments")
    c_avg_medicare = pick("average_medicare_payments","avg_mdcr_pymt_amt","avgmedicarepayments")
    return {
        "provider_id": c_provider_id,
        "provider_name": c_provider_name,
        "provider_city": c_provider_city,
        "provider_state": c_provider_state,
        "provider_zip_code": c_provider_zip,
        "ms_drg_definition": c_drg_desc,
        "ms_drg_code": c_drg_code,
        "total_discharges": c_total_discharges,
        "average_covered_charges": c_avg_cov,
        "average_total_payments": c_avg_total,
        "average_medicare_payments": c_avg_medicare
    }

async def load():
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://msuser:mspass@localhost:5432/msdrg")
    csv_url = os.getenv("ETL_CSV_URL")
    csv_path = os.getenv("ETL_CSV_PATH", "./data/sample_prices_ny.csv")
    ratings_path = os.getenv("RATINGS_CSV_PATH", "./data/ratings_seed.csv")
    src = csv_url if csv_url else csv_path
    df = pd.read_csv(
        src,
        dtype=str,
        encoding="cp1252",
        encoding_errors="replace"
    )
    mapping = map_columns(df)
    df = df.rename(columns={mapping[k]: k for k in mapping if mapping[k] is not None})
    # if "ms_drg_definition" in df.columns:
    #     df["ms_drg_definition"] = df["ms_drg_definition"].str.replace("–", "-", regex=False)
    if "ms_drg_code" not in df or df["ms_drg_code"].isna().all():
        df["ms_drg_code"] = df["ms_drg_definition"].apply(parse_drg_code_from_desc)
    for c in ["total_discharges","average_covered_charges","average_total_payments","average_medicare_payments","ms_drg_code"]:
        if c in df:
            if c == "ms_drg_code" or c == "total_discharges":
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
            else:
                df[c] = pd.to_numeric(df[c], errors="coerce")
    df["provider_zip_code"] = df["provider_zip_code"].apply(normalize_zip)
    df = df.dropna(subset=["provider_id","provider_name","ms_drg_definition"])
    engine = create_async_engine(url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        providers = df[["provider_id","provider_name","provider_city","provider_state","provider_zip_code"]].drop_duplicates("provider_id")
        for _, r in providers.iterrows():
            await session.execute(
                text("""
                INSERT INTO providers (provider_id, provider_name, provider_city, provider_state, provider_zip_code)
                VALUES (:provider_id, :provider_name, :provider_city, :provider_state, :provider_zip_code)
                ON CONFLICT (provider_id) DO UPDATE SET
                  provider_name=EXCLUDED.provider_name,
                  provider_city=EXCLUDED.provider_city,
                  provider_state=EXCLUDED.provider_state,
                  provider_zip_code=EXCLUDED.provider_zip_code
                """),
                {
                    "provider_id": str(r["provider_id"]),
                    "provider_name": str(r["provider_name"]),
                    "provider_city": to_str_or_none(r["provider_city"]),
                    "provider_state": to_str_or_none(r["provider_state"]),
                    "provider_zip_code": to_str_or_none(r["provider_zip_code"]),
                }
            )
        await session.commit()
        prices = df[["provider_id","ms_drg_definition","ms_drg_code","total_discharges","average_covered_charges","average_total_payments","average_medicare_payments"]]
        for _, r in prices.iterrows():
            await session.execute(
                text("""
                INSERT INTO drg_prices (provider_id, ms_drg_definition, ms_drg_code, total_discharges, average_covered_charges, average_total_payments, average_medicare_payments)
                VALUES (:provider_id, :ms_drg_definition, :ms_drg_code, :total_discharges, :average_covered_charges, :average_total_payments, :average_medicare_payments)
                """),
                {
                    "provider_id": str(r["provider_id"]),
                    "ms_drg_definition": str(r["ms_drg_definition"]),
                    "ms_drg_code": to_int_or_none(r["ms_drg_code"]),
                    "total_discharges": to_int_or_none(r["total_discharges"]),
                    "average_covered_charges": to_float_or_none(r["average_covered_charges"]),
                    "average_total_payments": to_float_or_none(r["average_total_payments"]),
                    "average_medicare_payments": to_float_or_none(r["average_medicare_payments"]),
                }
            )
        await session.commit()
        if Path(ratings_path).exists():
            rat = pd.read_csv(ratings_path)
            for _, r in rat.iterrows():
                await session.execute(
                    text("INSERT INTO ratings (provider_id, rating) VALUES (:pid, :rating)"),
                    {"pid": str(r["provider_id"]), "rating": int(r["rating"])}
                )
        else:
            prov_ids = providers["provider_id"].tolist()
            for pid in prov_ids:
                seed = sum(ord(ch) for ch in str(pid))
                rating = 1 + (seed % 10)
                await session.execute(
                    text("INSERT INTO ratings (provider_id, rating) VALUES (:pid, :rating)"),
                    {"pid": str(pid), "rating": int(rating)}
                )
        await session.commit()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(load())
