"""Local sandbox smoke: reporter -> actual HTTP judge calls -> SQLite -> outbox worker.
All external services are simulated; no actual browser automation or vendor API calls.
"""
import json,os,sys,urllib.request
base=os.getenv("AXQEOS_URL","http://api:8080")
token=os.environ["AX_REPORTER_TOKEN"]
def request(method,path,payload=None,headers=None):
 data=json.dumps(payload).encode() if payload is not None else None
 req=urllib.request.Request(base+path,data=data,method=method,headers={"Content-Type":"application/json",**(headers or {})})
 with urllib.request.urlopen(req,timeout=25) as response:return json.load(response)
def main():
 import time
 for i in range(30):
  try:
   assert request("GET","/health")["status"]=="ok";break
  except Exception:time.sleep(1)
 else:raise RuntimeError("API unavailable")
 import uuid
 external="lab-"+str(uuid.uuid4())
 result=request("POST","/api/v1/reporter",{"external_run_id":external,"test_id":"lab-smoke","goal":"Verify local HTTP chain","risk":0.4,"assertion_passed":True,"evidence_summary":"Synthetic pass assertion; simulated judge endpoints only"}, {"X-AX-Reporter-Token":token})
 assert result["tier"]=="T2" and result["outcome"]=="pass",result
 row=request("GET","/api/v1/runs/"+result["run_id"]+"/persistent")
 assert row["external_id"]==external
 print(json.dumps({"result":"PASS","scope":"LOCAL_SIMULATION_ONLY","run_id":result["run_id"],"tier":result["tier"]}))
if __name__=="__main__":main()
