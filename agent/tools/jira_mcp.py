import requests

def get_ticket_comments(jira_id: str) -> dict:
    response = requests.get(f"http://localhost:5001/jira/{jira_id}/comments")
    print("Fetching comments for JIRA ID:", jira_id)
    response.raise_for_status()
    return response.json()

def get_ticket_description(jira_id: str) -> dict:
    response = requests.get(f"http://localhost:5001/jira/{jira_id}/description")
    print("Fetching description for JIRA ID:", jira_id)
    response.raise_for_status()
    return response.json()