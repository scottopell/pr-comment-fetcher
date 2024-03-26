import requests
import argparse
import json
import os
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}
PR_COMMENTER = 'pr-commenter[bot]'
COMMENT_OF_INTEREST = "Regression Detector"

def get_comments_from_pr(user, repo, pr_number):
    comments_url = f'https://api.github.com/repos/{user}/{repo}/issues/{pr_number}/comments'
    comments = requests.get(comments_url, headers=HEADERS).json()

    comment_cnt = 0
    for comment in comments:
        if comment['user']['login'] == PR_COMMENTER and COMMENT_OF_INTEREST in comment['body']:
            return comment

        comment_cnt += 1



def get_comments_from_prs(user, repo, regression_comments_this_pr, max_prs):
    repo_key = f"{user}/{repo}"
    page = 1
    prs_processed = 0

    while prs_processed < max_prs:
        prs_url = f'https://api.github.com/repos/{user}/{repo}/issues?page={page}&state=all'
        resp = requests.get(prs_url, headers=HEADERS)
        print(f"Query for {page} returned status_code {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            return
        prs = resp.json()

        for pr in prs:
            if 'pull_request' not in pr:
                print(f"Skipping non-pull request issue #{number}")

            number = pr['number']
            if str(number) in regression_comments_this_pr:
                print(f"Skipping pr #{number} as already processed")
                prs_processed += 1
                continue

            regression_comment = get_comments_from_pr(user, repo, number)
            if regression_comment is not None:
                if number not in regression_comments_this_pr:
                    regression_comments_this_pr[number] = dict()
                prs_processed += 1
                # Store full comment for future processing
                regression_comments_this_pr[number]["regression_comment"] = regression_comment

                body = regression_comment["body"]
                # Extract run id and baseline/comparison SHAs as this is only immediately needed section
                run_id = re.search(r'Run ID: ([0-9a-h-]+)\s+', body).group(1)
                baseline = re.search(r'Baseline: ([0-9a-h]+)\s+', body).group(1)
                comparison = re.search(r'Comparison: ([0-9a-h]+)\s+', body).group(1)

                regression_comments_this_pr[number]["regression_run_id"] = run_id
                regression_comments_this_pr[number]["regression_baseline"] = baseline
                regression_comments_this_pr[number]["regression_comparison"] = comparison
                if pr['milestone'] is not None:
                    regression_comments_this_pr[number]["milestone_title"] = pr['milestone']['title']
        page += 1
    print(f"Processed {prs_processed} PRs")

    return regression_comments_this_pr


def main(org, repo, pages_to_fetch, json_cache_db_name):
    regression_comments = dict()
    try:
        with open(json_cache_db_name, 'r') as fp:
            regression_comments = json.loads(fp.read())
    except FileNotFoundError:
        print("No previous regression comments found, starting from scratch")

    existing_keys = regression_comments.keys()
    existing_keys_str = ", ".join([str(k) for k in existing_keys])
    print(f"Loaded {len(existing_keys)} Repos: {existing_keys_str}")
    repo_key = f"{org}/{repo}"
    if repo_key not in regression_comments:
        regression_comments[repo_key] = dict()
    comments = get_comments_from_prs(org, repo, regression_comments[repo_key], pages_to_fetch)
    regression_comments[repo_key] = comments

    with open(json_cache_db_name, 'w') as fp:
        json.dump(regression_comments, fp)

parser = argparse.ArgumentParser(description='GitHub Regression Comment Fetcher')

# Add arguments
parser.add_argument('org', type=str, help='GitHub organization')
parser.add_argument('repo', type=str, help='GitHub repository')
parser.add_argument('prs_to_fetch', type=int, help='Number of PRs to be fetched')
parser.add_argument("--json-cache-db", type=str, default="regression_comments_by_pr.json", help="JSON cache database file")

# Parse the command-line arguments
args = parser.parse_args()

main(args.org, args.repo, args.prs_to_fetch, args.json_cache_db)
