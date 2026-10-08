// Adapter for Node-based E2E runners; call report() from afterEach/onTestEnd hook.
export async function report(result) {
 const endpoint=process.env.AXQEOS_URL;
 const token=process.env.AX_REPORTER_TOKEN;
 if(!endpoint||!token) throw Error("AXQEOS_URL and AX_REPORTER_TOKEN required");
 const response=await fetch(endpoint.replace(/\/$/,"")+"/api/v1/reporter",{
  method:"POST",headers:{"Content-Type":"application/json","X-AX-Reporter-Token":token},
  body:JSON.stringify({
   external_run_id:result.external_run_id,
   test_id:result.test_id,
   goal:result.goal||"",
   risk:result.risk??0.5,
   assertion_passed:result.assertion_passed??null,
   evidence_uri:result.evidence_uri||null,
   evidence_summary:result.evidence_summary||""
  })
 });
 if(!response.ok) throw Error("AXQEOS reporter HTTP "+response.status);
 return response.json();
}
