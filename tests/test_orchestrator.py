import yaml
from app.orchestrator import route_assertion
policy=yaml.safe_load(open("config/routing.yaml"))["routing"]

def test_deterministic_fail_precedence():
 assert route_assertion(False,1,None,policy)==("T0","fail","assertion_failed")

def test_missing_assertion_requires_human():
 assert route_assertion(None,0.01,0.99,policy)[0]=="T3"

def test_critical_always_human():
 assert route_assertion(True,0.9,0.99,policy,complexity=0.1,budget=0)[0]=="T3"

def test_no_confidence_escalates():
 assert route_assertion(True,0.1,None,policy)[0]=="T2"

def test_low_confidence_escalates():
 assert route_assertion(True,0.1,0.4,policy)[0]=="T2"

def test_high_complexity_escalates():
 assert route_assertion(True,0.1,0.99,policy,complexity=0.9)[0]=="T2"

def test_high_confidence_low_risk_accepts():
 assert route_assertion(True,0.1,0.99,policy,complexity=0.1)==("T0","pass","deterministic_pass")

def test_budget_never_overrides_critical():
 assert route_assertion(True,0.95,0.99,policy,budget=0)[0]=="T3"
