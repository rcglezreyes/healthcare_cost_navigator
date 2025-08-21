import os
import json
import re
from typing import Dict, Any

def parse_question_offline(q: str) -> Dict[str, Any]:
    d = {}
    m = re.search(r"\bdrg\s*(\d{3})\b", q, re.IGNORECASE)
    if m:
        d["drg_code"] = int(m.group(1))
    m = re.search(r"\b(\d{5})\b", q)
    if m:
        d["zip"] = m.group(1)
    m = re.search(r"\b(\d+)\s*(?:km|kilometers|kilometres|miles|mi)\b", q, re.IGNORECASE)
    if m:
        v = float(m.group(1))
        if re.search(r"\bmi|miles\b", q, re.IGNORECASE):
            v = v * 1.60934
        d["radius_km"] = v
    if re.search(r"\bbest|highest|rating|quality\b", q, re.IGNORECASE):
        d["intent"] = "quality"
    else:
        d["intent"] = "cost"
    return d

async def parse_question_llm(q: str) -> Dict[str, Any]:
    key = os.getenv("OPENAI_API_KEY")
    if not key or os.getenv("ENABLE_LLM", "true").lower() != "true":
        return parse_question_offline(q)
    from openai import OpenAI
    client = OpenAI(api_key=key)
    system = "Return strict JSON with keys: drg_code:int optional, drg_text:str optional, zip:str optional, radius_km:float optional, intent in [cost,quality]. Convert miles to km."
    user = f"Question: {q}"
    r = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0
    )
    txt = r.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except Exception:
        return parse_question_offline(q)
