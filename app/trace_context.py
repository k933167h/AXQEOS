"""W3C Trace Context validation and correlation. Not a substitute for an OTel SDK."""
import re
import secrets
TRACEPARENT=re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
def traceparent(value=None):
    if value:
        match=TRACEPARENT.fullmatch(value.strip())
        if match and int(match.group(1),16) and int(match.group(2),16):
            return value.strip()
    return "00-"+secrets.token_hex(16)+"-"+secrets.token_hex(8)+"-01"
def trace_id(value):
    return traceparent(value).split("-")[1]
def child_traceparent(parent):
    valid=traceparent(parent)
    return "00-"+valid.split("-")[1]+"-"+secrets.token_hex(8)+"-"+valid.split("-")[3]
