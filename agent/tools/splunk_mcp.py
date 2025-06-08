def run_splunk_query(package_name: str, failure_time: str) -> str:
    # Simulate Splunk response
    return f"""
    ERROR Package install failed for {package_name}
    Caused by: java.lang.RuntimeException: Missing dependency
    """
