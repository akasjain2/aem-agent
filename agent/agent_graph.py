from langgraph.graph import StateGraph
from .tools.jira_mcp import get_ticket_info
from .tools.splunk_mcp import run_splunk_query
from .llm_config import llm
from typing import TypedDict

class AgentState(TypedDict, total=False):
    jira_id: str
    package_name: str
    failure_time: str
    logs: str
    diagnosis: str


def get_jira_node(state):
    jira = get_ticket_info(state["jira_id"])
    return {
        "package_name": jira.get("summary", "unknown"),
        "failure_time": "2024-06-01T10:23:00"  # static until Splunk timestamp added
    }

def get_splunk_node(state):
    logs = run_splunk_query(state["package_name"], state["failure_time"])
    return {"logs": logs}

def analyze_logs_node(state):
    prompt = f"Analyze the AEM log and explain failure:\n{state['logs']}"
    result = llm.invoke(prompt)
    return {"diagnosis": result}

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("jira", get_jira_node)
    builder.add_node("splunk", get_splunk_node)
    builder.add_node("analyze", analyze_logs_node)

    builder.set_entry_point("jira")
    builder.add_edge("jira", "splunk")
    builder.add_edge("splunk", "analyze")
    builder.set_finish_point("analyze")
    return builder.compile()
