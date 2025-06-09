from langgraph.graph import StateGraph
from .tools.jira_mcp import get_ticket_description, get_ticket_comments
from .tools.splunk_mcp import run_splunk_query
from .llm_config import llm
from typing import TypedDict
import re
import requests

class AgentState(TypedDict, total=False):
    jira_id: str
    package_name: str
    failure_time: str
    logs: str
    diagnosis: str
    summary: str
    description: str
    comments: list
    invocationTime: str
    completionTime : str
    actionId : str
    entityId : str
    instanceId : str
    topology: str


def get_jira_node(state):
    print("Input state in get_jira_node:", state)
    jira_desc = get_ticket_description(state["jira_id"])
    jira_comm = get_ticket_comments(state["jira_id"])
    result = {
        **state,
        "summary": jira_desc.get("summary", "unknown"),
        "description": jira_desc.get("description", "unknown"),
        "comments": [comment["body"] for comment in jira_comm.get("comments", [])],
        "failure_time": "2024-06-01T10:23:00"  # static until Splunk timestamp added
    }
    print("Output state in get_jira_node:", result)
    return result

def get_splunk_node(state):
    # print entire state
    print("Current state in get_splunk_node:", state)
    logs = run_splunk_query(state["summary"], state["failure_time"])
    return {"logs": logs}

def analyze_logs_node(state):
    prompt = f"Analyze the AEM log and explain failure:\n{state['logs']}"
    result = llm.invoke(prompt)
    return {"diagnosis": result}

def process_jira_with_llm_node(state):
    print("Current state in process_jira_with_llm_node:", state)
    description = state["description"]
    comments = state["comments"]
    summary = description + "\n" + "\n".join(comments)
    # LLM prompt to extract BigBear URLs
    prompt = (
        "You will be given text. Extract ONLY the valid URLs that match these domains: "
        "bb.ams.adobe.net, bigbear-enterprise.ent.ams-cloud.net, bigbear-prod.adobems.cn:8443. "
        "Return a **valid Python list**, and nothing else.\n\n"
        "Text:\n"
        f"{summary}"
    )

    url_list = llm.invoke(prompt)
    # After LLM invocation
    llm_output = url_list
    if isinstance(llm_output, dict) and "content" in llm_output:
        llm_output = llm_output["content"]
    elif hasattr(llm_output, "content"):
        llm_output = llm_output.content

    # Remove code block markers if present
    if llm_output.strip().startswith("```"):
        llm_output = llm_output.strip().strip("`")
        # Remove 'python' if present
        if llm_output.startswith("python"):
            llm_output = llm_output[len("python"):].strip()
    try:
        urls = eval(llm_output) if isinstance(llm_output, str) else llm_output
    except Exception:
        urls = []
    # Regex fallback if LLM fails
    if not urls:
        print("No URLs found by LLM")
        pattern = r"https?://(?:bb\\.ams\\.adobe\\.net|bigbear-enterprise\\.ent\\.ams-cloud\\.net|bigbear-prod\\.adobems\\.cn:8443)[^\s'\"]+"
        urls = re.findall(pattern, summary)
        print("URLs built manually:", urls)
    # If still no URLs, exit the chain with an error state
    if not urls:
        print("No URL could be built")
        return {**state, "error": "No BigBear URLs found in summary. Exiting chain."}
    # Try each URL
    for url in urls:
        # Remove /tail if present
        print("Processing URL:", url)
        if url.endswith("/tail"):
            url = url[:-5]
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print("Valid URL found:", url)
                data = resp.json()
                action_id = data.get("actionId", "")
                if action_id == "install-service-pack" or action_id == "install-client-packages":
                    entity_id = data.get("entityId", "")
                    # Extract the part like 'author1useast1-28434635' from entityId
                    match = re.search(r"<RESOURCE::[a-z0-9]+::([a-z0-9\-]+)>", entity_id)
                    extracted_entity = match.group(1) if match else None
                    # Fetch topology name from stripped URL
                    topology = None
                    if extracted_entity and match:
                        print("Extracted entity:", extracted_entity)
                        # Compose the topology URL using the full matched string
                        topology_url = "/".join(url.split("/")[:-3]) + "/"
                        try:
                            topology_resp = requests.get(topology_url, timeout=5)
                            if topology_resp.status_code == 200:
                                topology_json = topology_resp.json()
                                topology = topology_json.get("name")
                        except Exception:
                            pass

                    tail_url = url + "/tail"
                    tail_resp = requests.get(tail_url, timeout=5)
                    if tail_resp.status_code == 200:
                        bb_logs = tail_resp.text
                        print("Fetched tail content:")
                    else:
                        tail_content = None

                    return {
                        "invocationTime": data.get("invocationTime"),
                        "completionTime": data.get("completionTime"),
                        "actionId": action_id,
                        "entityId": entity_id,
                        "instanceId": extracted_entity,
                        "topology": topology,
                        "bbLogs": bb_logs
                        # Pass along previous state

                    }
        except Exception:
            continue
    # If none found, just return state
    return state

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("jira", get_jira_node)
    builder.add_node("process_jira_with_llm", process_jira_with_llm_node)
    builder.add_node("splunk", get_splunk_node)
    builder.add_node("analyze", analyze_logs_node)

    builder.set_entry_point("jira")
    builder.add_edge("jira", "process_jira_with_llm")
    builder.add_edge("process_jira_with_llm", "splunk")
    builder.add_edge("splunk", "analyze")
    builder.set_finish_point("analyze")
    return builder.compile()
