from app.trace_context import traceparent,child_traceparent,trace_id
def test_generate_valid_traceparent():
 value=traceparent()
 assert len(value)==55 and value.startswith("00-")
 assert traceparent(value)==value
def test_reject_invalid_and_zero_trace_id():
 assert traceparent("00-"+"0"*32+"-"+"1"*16+"-01")!="00-"+"0"*32+"-"+"1"*16+"-01"
 assert traceparent("untrusted")!="untrusted"
def test_child_retains_trace_id_new_span():
 parent=traceparent()
 child=child_traceparent(parent)
 assert trace_id(parent)==trace_id(child)
 assert parent!=child
