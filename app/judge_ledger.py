"""Append-only model-call usage ledger, with explicit unpriced records."""
import json
import math
import time
import uuid
from . import store
from .judge_metrics import judge_cost

def initialize():
    with store.connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS judge_calls(
            id TEXT PRIMARY KEY,run_id TEXT,model TEXT NOT NULL,tier TEXT NOT NULL,
            verdict TEXT NOT NULL,confidence REAL,latency_ms REAL NOT NULL,
            input_tokens INTEGER,output_tokens INTEGER,cost_usd REAL,
            status TEXT NOT NULL,created REAL NOT NULL)""")

def record_calls(run_id, calls, pricing=None):
    """Never infer token counts; unknown usage and cost remain NULL."""
    initialize()
    pricing=pricing or {}
    ids=[]
    with store.connect() as db:
        for call in calls:
            model=str(call.get("model") or "unknown")
            usage=call.get("usage") or {}
            input_tokens=usage.get("prompt_tokens")
            output_tokens=usage.get("completion_tokens")
            price=pricing.get(model)
            cost=None
            if price is not None and isinstance(input_tokens,int) and isinstance(output_tokens,int):
                cost=judge_cost(input_tokens=input_tokens,output_tokens=output_tokens,
                    input_usd_per_million=float(price["input_usd_per_million"]),
                    output_usd_per_million=float(price["output_usd_per_million"]))
            latency=float(call.get("latency_ms",0))
            if not math.isfinite(latency) or latency<0:raise ValueError("invalid latency")
            confidence=call.get("confidence")
            if confidence is not None:
                confidence=float(confidence)
                if not math.isfinite(confidence) or not 0<=confidence<=1:raise ValueError("invalid confidence")
            rid=str(uuid.uuid4())
            db.execute("INSERT INTO judge_calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(
                rid,run_id,model,str(call.get("tier","unknown")),
                str(call.get("verdict","review")),confidence,latency,
                input_tokens,output_tokens,cost,str(call.get("status","unknown")),time.time()))
            ids.append(rid)
    return ids

def summary(run_id):
    initialize()
    with store.connect() as db:
        rows=[dict(r) for r in db.execute("SELECT * FROM judge_calls WHERE run_id=? ORDER BY created,id",(run_id,))]
    priced=[r["cost_usd"] for r in rows if r["cost_usd"] is not None]
    return {"run_id":run_id,"calls":rows,"known_cost_usd":sum(priced),
            "unpriced_calls":len(rows)-len(priced),"cost_complete":len(priced)==len(rows) and bool(rows)}
