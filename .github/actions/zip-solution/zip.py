import os
import sys
import zipfile
from pathlib import Path

path = os.environ.get("SOLUTION_PATH", "")
github_output = os.environ["GITHUB_OUTPUT"]

if not path:
    print("Error: SOLUTION_PATH is not set")
    sys.exit(1)

source = Path(path)

EXCLUDED_DIRS = {".git", ".github"}

if not source.is_dir():
    print(f"Error: path '{source}' does not exist or is not a directory")
    sys.exit(1)

# --- Zip solution directory ---
zip_name = source.name if source.name else "solution"
zip_path = source.parent / f"{zip_name}.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for file in source.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in file.parts):
            continue
        if file.is_file():
            zf.write(file, file.relative_to(source))

print(f"Created {zip_path}")
with open(github_output, "a") as f:
    f.write(f"solutionZip={zip_path}\n")
