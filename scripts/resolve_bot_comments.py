#!/usr/bin/env python3
import subprocess
import json
import sys
import os

# Bot authors whose comments we want to resolve automatically
BOT_AUTHORS = [
    "sonarqubecloud",
    "trunk-io",
    "gemini-code-assist",
    "sentry",
    "github-actions"
]

def run_gh_command(args):
    """Run a gh CLI command and return the output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running gh command: {e.stderr}", file=sys.stderr)
        return None

def resolve_threads(pr_number):
    """Find and resolve unresolved review threads in a PR."""
    print(f"Checking PR #{pr_number} for unresolved bot comments...")
    
    # GraphQL query to get review threads
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $number) {
          reviewThreads(first: 100) {
            nodes {
              id
              isResolved
              comments(first: 1) {
                nodes {
                  author {
                    login
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    # Get owner and repo from git remote
    remote_url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
    # Handle both HTTPS and SSH URLs
    if remote_url.startswith("https://"):
        parts = remote_url.split("/")
        owner = parts[-2]
        repo = parts[-1].replace(".git", "")
    else: # SSH
        parts = remote_url.split(":")[-1].split("/")
        owner = parts[0]
        repo = parts[1].replace(".git", "")

    # Execute query
    result_json = run_gh_command([
        "api", "graphql",
        "-F", f"owner={owner}",
        "-F", f"repo={repo}",
        "-F", f"number={pr_number}",
        "-f", f"query={query}"
    ])
    
    if not result_json:
        return

    data = json.loads(result_json)
    threads = data.get("data", {}).get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])
    
    for thread in threads:
        if thread.get("isResolved"):
            continue
            
        comments = thread.get("comments", {}).get("nodes", [])
        if not comments:
            continue
            
        author = comments[0].get("author", {}).get("login")
        if author in BOT_AUTHORS:
            print(f"Resolving thread {thread['id']} by {author}...")
            
            # Mutation to resolve thread
            mutation = """
            mutation($id: ID!) {
              resolveReviewThread(input: {threadId: $id}) {
                thread {
                  id
                  isResolved
                }
              }
            }
            """
            
            run_gh_command([
                "api", "graphql",
                "-f", f"query={mutation}",
                "-F", f"id={thread['id']}"
            ])

def main():
    # If PR number is provided as argument, use it
    if len(sys.argv) > 1:
        for pr_arg in sys.argv[1:]:
            resolve_threads(int(pr_arg))
    else:
        # Otherwise, get all open PRs
        pr_list_json = run_gh_command(["pr", "list", "--state", "open", "--json", "number"])
        if pr_list_json:
            prs = json.loads(pr_list_json)
            for pr in prs:
                resolve_threads(pr["number"])

if __name__ == "__main__":
    main()
