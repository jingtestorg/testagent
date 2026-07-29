import json
import os
import sys
import urllib.request

sci_token = os.environ.get("SCI_TOKEN", "")
api_base_url = os.environ.get("SOLUTION_HANDLING_API_BASE_URL", "")
solution_id = os.environ.get("SOLUTION_ID", "")

# --- Validate inputs ---
errors = []
if not sci_token:
    errors.append("input 'sciToken' is required but not set")
if not api_base_url:
    errors.append("input 'solutionHandlingApiBaseUrl' is required but not set")
if not solution_id:
    errors.append("input 'solutionId' is required but not set")
if errors:
    for e in errors:
        print(f"Error: {e}")
    sys.exit(1)

print(f"::add-mask::{sci_token}")

# --- Deploy solution ---
req = urllib.request.Request(
    f"{api_base_url}/{solution_id}/versions/main/deploy",
    data=b"",
    method="POST",
    headers={"Authorization": f"Bearer {sci_token}"},
)
try:
    with urllib.request.urlopen(req) as resp:
        response = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"Error: deploy request failed with status {e.code}: {e.read().decode()}")
    sys.exit(1)

print(json.dumps(response, indent=2))
