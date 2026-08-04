import base64
import json
import os
import sys
import urllib.request

sci_token = os.environ.get("SCI_TOKEN", "")
api_base_url = os.environ.get("SOLUTION_HANDLING_API_BASE_URL", "")
solution_zip = os.environ.get("SOLUTION_ZIP", "")
github_output = os.environ["GITHUB_OUTPUT"]

# --- Validate inputs ---
errors = []
if not sci_token:
    errors.append("input 'sciToken' is required but not set")
if not api_base_url:
    errors.append("input 'solutionHandlingApiBaseUrl' is required but not set")
if not solution_zip:
    errors.append("input 'solutionZip' is required but not set")
if errors:
    for e in errors:
        print(f"Error: {e}")
    sys.exit(1)

print(f"::add-mask::{sci_token}")

# --- Import solution ---
with open(solution_zip, "rb") as f:
    zip_b64 = base64.b64encode(f.read()).decode()

payload = json.dumps({
    "overwrite": True,
    "semanticVersion": "main",
    "zip": zip_b64,
}).encode()

req = urllib.request.Request(
    f"{api_base_url}/importZip",
    data=payload,
    method="POST",
    headers={
        "Authorization": f"Bearer {sci_token}",
        "Content-Type": "application/json",
    },
)
try:
    with urllib.request.urlopen(req) as resp:
        response = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"Error: import request failed with status {e.code}: {e.read().decode()}")
    sys.exit(1)

print(json.dumps(response, indent=2))

solution_id = response.get("solutionId")
if not solution_id:
    print("Error: solutionId not found in response")
    sys.exit(1)

with open(github_output, "a") as f:
    f.write(f"solutionId={solution_id}\n")
