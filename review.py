import argparse
import os
import subprocess
from pathlib import Path

import boto3
import requests

# max number of Git diff data sent to the LLM 
# This prevents large pull requests and using excessive tokens 
MAX_DIFF_BYTES = 100 * 1024

# Use the model supplied by yhe env variable 
# Otherwise default to the lower cost Claude Haiku Model 
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "au.anthropic.claude-haiku-4-5-20251001-v1:0",
)

# Default AWS region used for Bedrock
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

# Skipping files that do not provide value 
# e.g. Lock Files are excluded from the diff analysis 
SKIP_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "uv.lock",
}

# Binary or non-text files also excluded
# This reviewer only looks at text-based source-code diffs
SKIP_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
}

# Collecting changed files and their diffs from Git 
def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout

# Reeturn true if a changed file should not be sent for AI reviewer
# If it contains name matching those in SKIP_FILENAMES
def should_skip(filename):
    path = Path(filename)

    if path.name.lower() in SKIP_FILENAMES:
        return True

    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True

    return False


# Collect reviewable Git changes relative to the supplied Git reference
def get_diff(diff_ref):
    files = run_git(
        "diff",
        "--name-only",
        diff_ref,
        "--",
    ).splitlines()

    # Store valid code diffsa nd keep track of files intentionally skipped
    chunks = []
    skipped = []
    total_bytes = 0

    for filename in files:
        if should_skip(filename):
            skipped.append(filename)
            continue

        file_diff = run_git(
            "diff",
            "--no-ext-diff",
            "--unified=3",
            diff_ref,
            "--",
            filename,
        )

        if not file_diff.strip():
            continue

            # Calculate the size of the diff in bytes and check if it exceeds the maximum allowed size
        size = len(file_diff.encode("utf-8"))

        if total_bytes + size > MAX_DIFF_BYTES:
            return None, skipped, True

        # Stop the review if total diff exceeds the limit 
        # controls both the context size and Bedrock inference costs
        chunks.append(file_diff)
        total_bytes += size

    # Combine each file's diff into one text block for the LLM 
    return "\n".join(chunks), skipped, False

# Send the Git diff to Claude via Amazon Bedrock 
def call_bedrock(diff):
    profile = os.getenv("AWS_PROFILE")

    session_args = {
        "region_name": AWS_REGION,
    }

    if profile:
        session_args["profile_name"] = profile

    # Create authenticated AWS session
    session = boto3.Session(**session_args)
    # bedrock-runtime is the API used to send inference requests to models 
    client = session.client("bedrock-runtime")

    # Load the code review instructions seaprately
    system_prompt = Path("prompt.md").read_text()

    # Send the review instructions as the system message and Git diff as the user message
    response = client.converse(
        modelId=MODEL_ID,
        system=[
            {
                "text": system_prompt,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            "Review the following Git diff:\n\n"
                            + diff
                        )
                    }
                ],
            }
        ],
        # Limiting response length and temperature low 
        # Code reviews are consistent between runs 
        # Temperature = randomness, creativity 
        inferenceConfig={
            "maxTokens": 2000,
            "temperature": 0.1,
        },
    )
    # Extract response content returned by Bedrock
    content = response["output"]["message"]["content"]
    # Combine all text blocks into a single .md review 
    review = "\n".join(
        block["text"]
        for block in content
        if "text" in block
    )
    #return both the review and the token use for monitoring/cost awareness for user 
    return review, response["usage"]

# Constructing the final .md comment to appear on the pull request 
def build_comment(review, usage, skipped):
    body = review

    # Tells us which changed files intentionally excluded 
    if skipped:
        body += "\n\n### Skipped files\n"
        body += "\n".join(f"- `{name}`" for name in skipped)

    # Add model info for transparency 
    body += "\n\n---\n"
    body += f"_Model: `{MODEL_ID}`"

    # include token use total so AI consumption is tracked 
    if usage:
        body += (
            f" · Input tokens: {usage['inputTokens']}"
            f" · Output tokens: {usage['outputTokens']}"
            f" · Total tokens: {usage['totalTokens']}_"
        )
    else:
        body += " · Bedrock was not called._"

    return body

# Show/post the generated AI review to the current Github pull request 
def post_comment(body):
    token = os.environ["GITHUB_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]

    # pull requests can receive general comments through GitHub's issues Comments REST API 
    url = (
        f"https://api.github.com/repos/"
        f"{repository}/issues/{pr_number}/comments"
    )
    # Authenticated using the temporary GITHUB_TOKEN created for the workflow
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        json={"body": body},
        timeout=30,
    )

    response.raise_for_status()

# The complete AI reviewer workflow
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--diff-ref",
        default="main",
        help="Git reference/range to compare against",
    )
    # dry run allows the AI review to be tested locally without posting to Github
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print review instead of posting to GitHub",
    )

    args = parser.parse_args()

    diff, skipped, too_large = get_diff(args.diff_ref)

    if too_large:
        review = (
            "# AI Code Review\n\n"
            "Diff too large for automated review. "
            "The review was skipped because the reviewable "
            "diff exceeded 100 KB."
        )
        usage = None

    elif not diff:
        review = (
            "# AI Code Review\n\n"
            "No reviewable text changes found."
        )
        usage = None

    else:
        review, usage = call_bedrock(diff)

    comment = build_comment(review, usage, skipped)

    if args.dry_run:
        print(comment)
    else:
        post_comment(comment)
        print("AI review posted successfully.")


if __name__ == "__main__":
    main()