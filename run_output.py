import json, subprocess, sys

# Run: python3 /project/narrative-nexus/output_results.py
result = subprocess.run(["python3", "/project/narrative-nexus/output_results.py"], capture_output=True, text=True)
print(result.stdout)
