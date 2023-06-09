SMP's regression detector bot leaves comments on the agent PRs that have the run-id and a summary table of analysis.

This tool will look through all PRs in a given repo and find the ones left by this bot name and capture them into a json db file.

```
# Make sure GH_TOKEN env var is set
# To fetch 50 PRs that contain a regression detector comment
python3 main.py datadog datadog-agent 50
```

## Viewing the regression data
`jq` can do some basic filtering and reformatting, however there is a go parser
in `./go-parser` that is much faster and parses the actual HTML as well for even
simpler formatting

#### `jq` example
To utilize the JSON db file, `jq` can be used.

```
jq '."datadog/datadog-agent" | to_entries[] | select(.value.milestone_title == "7.46.0") | "https://github.com/DataDog/datadog-agent/pull/\(.key) Run-ID: \(.value.regression_run_id)"' regression_comments_by_pr.json
```

#### `go-parser`
```
$ cd go-parser
$ go run main.go | awk ' {print $3, $6, $7, $8, $9, $10}' | sort -n
<snip>
https://github.com/datadog/datadog-agent/pull/17447 throughput -0.37 [-1.42, +0.67] 35.44%]
https://github.com/datadog/datadog-agent/pull/17452 throughput +0.14 [-0.89, +1.17] 13.95%]
https://github.com/datadog/datadog-agent/pull/17465 throughput +0.19 [-0.87, +1.24] 17.86%]
https://github.com/datadog/datadog-agent/pull/17473 throughput +0.62 [-0.41, +1.65] 56.06%]
https://github.com/datadog/datadog-agent/pull/17489 throughput +0.23 [-0.79, +1.25] 22.62%]
https://github.com/datadog/datadog-agent/pull/17491 throughput -0.36 [-1.37, +0.65] 35.23%]
https://github.com/datadog/datadog-agent/pull/17532 throughput +0.39 [-0.64, +1.42] 37.35%]
https://github.com/datadog/datadog-agent/pull/17582 throughput +0.80 [-0.24, +1.83] 67.79%]
https://github.com/datadog/datadog-agent/pull/17588 throughput +1.85 [+0.80, +2.89] 97.67%]
https://github.com/datadog/datadog-agent/pull/17593 throughput +0.87 [-0.17, +1.91] 71.57%]
https://github.com/datadog/datadog-agent/pull/17692 throughput +0.44 [-0.58, +1.46] 41.59%]
```
