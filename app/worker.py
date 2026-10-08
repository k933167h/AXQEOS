import os,json,asyncio,logging,httpx
from . import store
logging.basicConfig(level=logging.INFO)
async def deliver(job):
 row=store.get_run(job["run_id"])
 if not row:raise RuntimeError("missing run")
 payload=json.loads(row["payload"])
 dest=job["destination"]
 if dest=="plane":
  url=os.getenv("PLANE_ISSUE_URL");token=os.getenv("PLANE_API_KEY")
  if not url or not token:raise RuntimeError("Plane not configured")
  headers={"X-API-Key":token}
  body={"name":"AXQEOS failed: "+payload.get("test_id","unknown"),"description_html":"<p>Run: "+row["id"]+"</p><p>Evidence: "+str(payload.get("evidence_uri") or "none")+"</p>"}
 elif dest=="kiwi":
  url=os.getenv("KIWI_RESULT_URL");token=os.getenv("KIWI_API_TOKEN")
  if not url or not token:raise RuntimeError("Kiwi adapter endpoint not configured")
  headers={"Authorization":"Bearer "+token}
  body={"external_run_id":row["id"],"test_id":payload.get("test_id"),"status":row["outcome"],"evidence_uri":payload.get("evidence_uri")}
 elif dest=="langfuse":
  url=os.getenv("LANGFUSE_INGEST_URL");token=os.getenv("LANGFUSE_INGEST_TOKEN")
  if not url or not token:raise RuntimeError("Langfuse ingest adapter not configured")
  headers={"Authorization":"Bearer "+token}
  body={"run_id":row["id"],"test_id":payload.get("test_id"),"outcome":row["outcome"],"tier":row["tier"],"evidence_uri":payload.get("evidence_uri")}
 else:raise RuntimeError("unknown destination")
 headers["Idempotency-Key"]=row["id"]+":"+dest
 async with httpx.AsyncClient(timeout=15) as client:
  res=await client.post(url,json=body,headers=headers);res.raise_for_status()
  try:return str(res.json().get("id") or res.json().get("result",{}).get("id") or "accepted")
  except Exception:return "accepted"
async def run_once():
 for job in store.pending():
  try:store.finish(job,await deliver(job))
  except Exception as exc:
   logging.exception("Delivery failed for %s",job["id"]);store.retry(job,exc)
async def main():
 store.init()
 while True:
  await run_once();await asyncio.sleep(5)
if __name__=="__main__":asyncio.run(main())
