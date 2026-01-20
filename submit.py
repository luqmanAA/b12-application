import json
import hmac
import hashlib
import datetime
import requests
import os
import sys


def submit_application():
    # 1. Fetching all configuration from environment variables
    secret = os.getenv("B12_SIGNING_SECRET")
    url = os.getenv("B12_SUBMISSION_URL")
    name = os.getenv("USER_FULL_NAME")
    email = os.getenv("USER_EMAIL")
    resume_link = os.getenv("USER_RESUME_LINK")

    # building repo url
    repo_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}"
    run_id = os.getenv('GITHUB_RUN_ID')

    # Validating that all required secrets are present
    required_vars = [secret, url, name, email, resume_link]
    if not all(required_vars):
        print("Error: One or more required environment variables are missing.")
        sys.exit(1)

    # 2. Constructing Payload
    # Using Z for UTC and ensuring 3 decimal places for milliseconds
    payload = {
        "timestamp": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(timespec='milliseconds').replace("+00:00","Z"),
        "name": name,
        "email": email,
        "resume_link": resume_link,
        "repository_link": repo_url,
        "action_run_link": f"{repo_url}/actions/runs/{run_id}"
    }

    # 3. Canonicalizing JSON: Sorting keys alphabetically and removing whitespace
    compact_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    payload_bytes = compact_json.encode('utf-8')

    # 4. Generating HMAC-SHA256 Signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    # 5. Executing POST Request
    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": f"sha256={signature}"
    }

    response = None
    try:
        response = requests.post(url, data=payload_bytes, headers=headers)
        response.raise_for_status()

        result = response.json()
        print(f"Submission Successful!")
        print(f"Receipt: {result.get('receipt')}")

    except requests.exceptions.RequestException as e:
        print(f"Submission Failed: {e}")
        if response is not None:
            print(f"Response: {response.text}")
        sys.exit(1)


if __name__ == "__main__":
    submit_application()