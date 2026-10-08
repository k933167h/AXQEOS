from app.main import Run,route

def test_fail_closed():
 assert route(Run(test_id='t',risk=0.1,assertion_passed=False))[1]=='fail'
 assert route(Run(test_id='t',risk=0.1,assertion_passed=None))[1]=='review'

def test_critical_review():
 assert route(Run(test_id='t',risk=0.99,assertion_passed=True,confidence=1))[0]=='T3'
