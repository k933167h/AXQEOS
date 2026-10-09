import asyncio
from unittest.mock import AsyncMock,patch
from app import judges

def test_critical_skips_model_calls():
 with patch.object(judges,"judge",new_callable=AsyncMock) as mock:
  tier,outcome,detail=asyncio.run(judges.evaluate("evidence",0.9))
  assert (tier,outcome)==("T3","review")
  mock.assert_not_awaited()

def test_complexity_bypasses_cheap_judge():
 with patch.object(judges,"judge",new_callable=AsyncMock,return_value={"verdict":"pass","confidence":0.98,"reason":"verified"}) as mock:
  tier,outcome,_=asyncio.run(judges.evaluate("evidence",0.1,0.95))
  assert (tier,outcome)==("T2","pass")
  assert mock.await_count==1

def test_low_confidence_escalates():
 async def fake_judge(*args,**kwargs):
  return {"verdict":"review","confidence":0.3,"reason":"uncertain"} if args[1]=="cheap" else {"verdict":"pass","confidence":0.98,"reason":"verified"}
 with patch.object(judges,"judge",side_effect=fake_judge):
  with patch.dict("os.environ",{"JEV_MODEL":"cheap","LLM_JUDGE_MODEL":"strong"}):
   assert asyncio.run(judges.evaluate("evidence",0.1))[0]=="T2"
