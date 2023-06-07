SMP's regression detector bot leaves comments on the agent PRs that have the run-id and a summary table of analysis.

This tool will look through all PRs in a given repo and find the ones left by this bot name and capture them into a json db file.

```
# Make sure GH_TOKEN env var is set
# To fetch 50 PRs that contain a regression detector comment
python3 main.py datadog datadog-agent 50
```

To utilize the JSON db file, `jq` can be used.

```
jq '."datadog/datadog-agent" | to_entries[] | select(.value.milestone_title == "7.46.0") | "https://github.com/DataDog/datadog-agent/pull/\(.key) Run-ID: \(.value.regression_run_id)"' regression_comments_by_pr.json
```
