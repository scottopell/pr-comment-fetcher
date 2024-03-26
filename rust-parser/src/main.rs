use clap::Parser;
use serde::{Deserialize, Serialize};
use serde_json::Result;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

/// This application processes PR information from a given JSON file.
#[derive(Parser, Debug)]
#[clap(author, version, about, long_about = None)]
struct Args {
    /// The milestone to filter PRs by
    #[clap(short, long)]
    milestone: Option<String>,

    /// The PR Number of interest
    #[clap(long)]
    pr_num: Option<String>,

    /// The name of the repository
    #[clap(short, long)]
    repo: Option<String>,

    /// Path to the JSON file containing PR data
    #[clap(short, long, parse(from_os_str))]
    path: PathBuf,
}

#[derive(Serialize, Deserialize, Debug)]
struct Comment {
    url: String,
    body: String,
    html_url: String,
    issue_url: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct PR {
    merged: Option<bool>,
    merge_commit_sha: Option<String>,
    milestone_title: Option<String>,
    regression_comment: Option<Comment>,
    regression_baseline: Option<String>,
    regression_comparison: Option<String>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let data = fs::read_to_string(args.path.clone())
        .unwrap_or_else(|_| format!("Unable to read file: {:?}", args.path));

    // Deserialize into a HashMap where the key is the repo name and the value is another HashMap of PRs
    let repos: HashMap<String, HashMap<String, PR>> = serde_json::from_str(&data)?;

    if let Some(repo_of_interest) = args.repo {
        if let Some(pr_num) = args.pr_num {
            if let Some(prs) = repos.get(&repo_of_interest) {
                if let Some(pr) = prs.get(&pr_num) {
                    println!("PR: {:#?}", pr);
                } else {
                    println!("No PR found for PR Number: {}", pr_num);
                }
            } else {
                println!("No PRs found for repo: {}", repo_of_interest);
            }
        } else if let Some(prs) = repos.get(&repo_of_interest) {
            filter_and_summarize(prs, args.milestone.as_deref());
        } else {
            println!("No PRs found for repo: {}", repo_of_interest)
        }
    } else {
        for (repo, _) in repos.iter() {
            println!("Repos: {}", repo);
        }
    }

    Ok(())
}

fn filter_and_summarize(prs: &HashMap<String, PR>, milestone_filter: Option<&str>) {
    let filtered: Vec<&PR> = prs
        .values()
        .filter(|pr| {
            match (&pr.milestone_title, &milestone_filter) {
                (Some(title), Some(filter)) => title == filter,
                (None, Some(_)) => false,
                _ => true, // Include all PRs if no milestone filter is specified
            }
        })
        .collect();

    // Summarize
    let total = filtered.len();
    let merged = filtered.iter().filter(|pr| pr.merged.unwrap_or(false));
    let merged_count = merged.clone().count();

    let mut merged_with_regression = 0;
    println!("Merged PRs with either a Regression or an Improvement:");
    println!("=====================");
    for pr in merged {
        if let Some(comment) = &pr.regression_comment {
            if comment
                .body
                .contains("No significant changes in experiment optimization goals")
            {
                continue;
            }
            let (_, details) = match comment
                .body
                .split_once("Significant changes in experiment optimization goals")
            {
                Some((_, details)) => ("", details),
                None => panic!("Unknown regression detector comment: {:#?}", comment.body),
            };
            let (details, _) = match details.split_once("Experiments ignored for regressions") {
                Some((details, _)) => (details, ""),
                None => panic!("Unknown regression detector comment: {:#?}", comment.body),
            };
            let improvements = details.match_indices('✅').count();
            let regressions = details.match_indices('❌').count();
            if regressions > 0 {
                merged_with_regression += 1;
            }
            if improvements > 0 || regressions > 0 {
                println!(
                    "Improvements: {improvements}, Regressions: {regressions} {url}",
                    url = comment.html_url
                );
            }
        }
    }
    let not_merged = total - merged_count;

    println!("=====================");
    println!("Total PRs: {}", total);
    println!("Merged: {}", merged_count);
    println!("Not Merged: {}", not_merged);
    println!("Merged with regression: {}", merged_with_regression);
}
