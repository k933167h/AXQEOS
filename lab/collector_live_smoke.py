"""Send an actual OTLP/HTTP JSON span to a local Docker Collector.

Local experiment only; uses loopback, no secrets or customer content.
"""
import json
import sys
import time
import urllib.request

TRACE="0123456789abcdef0123456789abcdef"
SPAN="0123456789abcdef"
NAME="axqeos.collector.smoke"

def payload():
    now=str(time.time_ns())
    return {"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"axqeos-pilot-smoke"}}]},
      "scopeSpans":[{"scope":{"name":"axqeos.collector.smoke"},"spans":[{
      "traceId":TRACE,"spanId":SPAN,"name":NAME,
      "startTimeUnixNano":now,"endTimeUnixNano":now,
      "attributes":[{"key":"axqeos.test","value":{"stringValue":"synthetic"}}]}]}]}]}

def send(url="http://127.0.0.1:4318/v1/traces"):
    body=json.dumps(payload()).encode("utf-8")
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=10) as response:
        if response.status not in (200,202):raise RuntimeError("OTLP receiver rejected span")
    return {"trace_id":TRACE,"span_id":SPAN,"name":NAME,"receiver_acknowledged":True}

if __name__=="__main__":
    print(json.dumps(send(sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:4318/v1/traces")))
