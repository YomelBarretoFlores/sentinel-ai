from ..api.state import AGENT_STATE



def check_stop():
    if AGENT_STATE.get("stop_requested"):
        raise RuntimeError("Agent stopped by user")
