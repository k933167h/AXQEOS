"""LOCAL LAB ONLY. Simulates judge, Kiwi, Langfuse, and Plane HTTP endpoints.
Never use this as evidence of vendor integration or model evaluation quality.
"""
import json,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=="/health":return self.reply(200,{"status":"ok","simulation":True})
  self.reply(404,{"error":"not_found"})
 def do_POST(self):
  size=int(self.headers.get("Content-Length","0"))
  if size>100000:self.reply(413,{"error":"too_large"});return
  try:body=json.loads(self.rfile.read(size))
  except Exception:self.reply(400,{"error":"bad_json"});return
  path=urlparse(self.path).path
  if path.endswith("/chat/completions"):
   model=body.get("model","")
   confidence=0.45 if model=="mock-jev" else 0.97
   result={"verdict":"pass","confidence":confidence,"reason":"SIMULATED_NOT_REAL_JUDGE"}
   return self.reply(200,{"choices":[{"message":{"content":json.dumps(result)}}]})
  if path in ("/kiwi/results","/langfuse/events","/plane/issues"):
   if not self.headers.get("Idempotency-Key"):return self.reply(400,{"error":"idempotency_required"})
   return self.reply(201,{"id":"simulated-"+path.split("/")[1],"simulation":True})
  self.reply(404,{"error":"not_found"})
 def reply(self,status,body):
  data=json.dumps(body).encode()
  self.send_response(status);self.send_header("Content-Type","application/json")
  self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
 def log_message(self,fmt,*args):print("lab",fmt%args,flush=True)
if __name__=="__main__":
 ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","8090"))),Handler).serve_forever()
