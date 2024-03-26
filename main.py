from datetime import datetime, timezone
import requests
import argparse
import json
import os
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}
PR_COMMENTER = 'pr-commenter[bot]'
COMMENT_OF_INTEREST = "Regression Detector"

def make_gh_request(url):
    print(f"making request to {url}")
    resp = requests.get(url, headers=HEADERS)
    while resp.status_code == 429 or resp.status_code == 403:
        if 'Retry-After' in resp.headers:
            retry_after = int(resp.headers['Retry-After'])
            print(f"Got rate limited, instructed to retry after {retry_after} seconds. Sleeping...")
            sleep(retry_after)
            resp = requests.get(pr_details_url)
        elif 'X-RateLimit-Reset' in resp.headers:
            sleep_until = int(resp.headers['X-RateLimit-Reset'])
            sleep_duration = sleep_until - datetime.now(timezone.utc)
            print(f"Got rate limited, sleeping until {sleep_until} -- which is {sleep_duration} seconds")
            sleep(sleep_duration)

        else:
            print(f"Got rate limited with no retry... headers: {resp.headers}")
            return None

    return resp


def get_comments_from_pr(user, repo, pr_number):
    comments_url = f'https://api.github.com/repos/{user}/{repo}/issues/{pr_number}/comments'
    resp = make_gh_request(comments_url)
    if resp == None:
        return None
    comments = resp.json()

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
        resp = make_gh_request(prs_url)
        if resp is None:
            print("Couldn't fetch list of PRs, skipping to next one")
            continue;

        prs = resp.json()

        for pr in prs:
            if 'pull_request' not in pr:
                print(f"Skipping non-pull request issue")
                continue

            number = pr['number']
            if str(number) in regression_comments_this_pr:
                print(f"Skipping pr #{number} as already processed")
                prs_processed += 1
                continue
            else:
                regression_comments_this_pr[number] = dict()

            pr_details_url = f"https://api.github.com/repos/{user}/{repo}/pulls/{number}"
            pr_details_resp = make_gh_request(pr_details_url)
            if pr_details_resp is None:
                print(f"Got no response for request to {pr_details_url}, skpping {number}")
                continue

            pr_details = pr_details_resp.json()

            regression_comments_this_pr[number]['merged'] = pr_details['merged']
            regression_comments_this_pr[number]['merge_commit_sha'] = pr_details['merge_commit_sha']

            regression_comment = get_comments_from_pr(user, repo, number)
            if regression_comment is not None:
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
