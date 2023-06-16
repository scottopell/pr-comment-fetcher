Parses through raw github regression detector tables and prints summary line for
each PR


Looks for `../regression_comments_by_pr.json` as the input file by default

```
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

