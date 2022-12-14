import json
import os
from pathlib import Path
import time

from utils.runners import run_marketplace

# Settings to run a negotiation session:
#   You need to specify the classpath of 2 agents to start a negotiation. Parameters for the agent can be added as a dict (see example)
#   You need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   You need to specify a time deadline (is milliseconds (ms)) we are allowed to negotiate before we end without agreement.

# [Conceder, Boulware, Hardliner, MiCRO]
dist = [0.25, 0.25, 0.25, 0.25]
domain = "basic"
deadline = 10000
endtime = 500.0
count = 3000
marketplace_settings = {
    "agent_distribution": dist,
    "profile_set": "domains/" + domain,
    "deadline_time_ms": deadline,
    "endtime": endtime,
    "count": count,
}

RESULTS_DIR = Path("results", str(dist) + " " + str(domain) + " " + str(endtime))

# create results directory if it does not exist
if not RESULTS_DIR.exists():
    RESULTS_DIR.mkdir(parents=True)

# run a session and obtain results in dictionaries
marketplace_steps, marketplace_results, marketplace_results_summary = run_marketplace(marketplace_settings)

# save the marketplace settings for reference
with open(RESULTS_DIR.joinpath("marketplace_steps.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(marketplace_steps, indent=2))
# save the marketplace results
with open(RESULTS_DIR.joinpath("marketplace_results.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(marketplace_results, indent=2))
# save the marketplace results summary
marketplace_results_summary.to_csv(RESULTS_DIR.joinpath("marketplace_results_summary.csv"))
