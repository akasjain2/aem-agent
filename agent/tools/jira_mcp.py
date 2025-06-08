import requests

def get_ticket_info(jira_id: str) -> dict:
    response = requests.get(f"http://localhost:5001/jira/{jira_id}/description")
    response.raise_for_status()
    return response.json()
