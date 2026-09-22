# AI DevOps Code Reviewer 
An AI-assisted code reviewer that reviews pull requests using Claude (via AWS Bedrock) and posts the results as a PR comment.

The purpose of this project was to streamline the workflow of reviewing code changes when a Pull Request (PR) is updated or opened. The workflow extracts the PR diff, sending it to AWS Bedrock hosted Claude model (Haiku) and posts feedback to the pull request as comments. 

The goal is to demonstrate a practical DevOps workflow that combines CI/CD automation, cloud authentication, AWS, AI-assisted code reviews, secure AWS access, cost controls and repeatable testing. 

## What it does
 
When run against a pull request, the script:
 
1. Gets the Git diff between the PR branch and a reference branch (e.g. `main`)
2. Skips irrelevant files (lock files, images, binaries)
3. Sends the diff to Claude, along with a review prompt, via AWS Bedrock
4. Posts the AI-generated review as a comment on the GitHub pull request
The review checks for bugs, security issues, performance problems, missing error handling and missing tests, and sorts findings into **Critical**, **Warning** and **Suggestion** sections.

## Project Intentions 
This project was built to:

- Automatically review pull-request code changes
- Detect security, reliability, logic, maintainability, and performance issues
- Integrate GitHub Actions with Amazon Bedrock
- Authenticate GitHub Actions to AWS using OIDC instead of long-lived credentials
- Use least-privilege IAM permissions
- Control AI usage and cost
- Re-run reviews when a pull request changes and synchronises
- Avoid duplicate AI comments
- Allow reviews to be skipped using a GitHub label
- Evaluate the reviewer using controlled test cases

## Architecture

```text
Developer
   ↓
Feature / Test Branch
   ↓
Pull Request
   ↓
GitHub Actions
   ↓
Checkout PR Head Commit
   ↓
Extract Git Diff
   ↓
GitHub OIDC
   ↓
AWS IAM Role
   ↓
Amazon Bedrock
   ↓
Claude Haiku
   ↓
Structured AI Review
   ↓
GitHub Pull Request Comment
```

The workflow is triggered by pull-request events rather than direct pushes to `main`.
This ensures that ...

## Technology Stack

- **GitHub**
  - Git repositories
  - Pull requests
  - GitHub Actions
  - GitHub REST API

- **AWS**
  - Amazon Bedrock (boto3) 
  - AWS IAM
  - GitHub OIDC 

- **AI Model**
  - Claude Haiku 4.5

- **Development**
  - Python 3.12
  - boto3
  - requests
  - Git
  - VS Code

## Setup
 
```bash
pip install -r requirements.txt
```
Also need: 
- AWS credentials with Bedrock access
- Github account with permission to comment on PRs

## Branches & Testing 
This project used short-lived branhces to try out the AI reviewer before changes are mergedi nto main. None of the `test/*` branches contain real application changes with each one planting a deliberate issue in `sample_app/` to open up a PR so that the reviewer's comment can be checked against a known result. 

### `main'
The working version of the project: `review.py`, the review instructions (`prompt.md`), the GitHub Actions workflow (`.github/workflows/ai-review.yml`), and `sample_app/` is a folder used as the target for test pull requests.

### `test-ai-review`
 
An early branch used while first setting up the GitHub Actions workflow and the AWS Bedrock connection. It included two temp scripts (`tests/test_aws.py`, `tests/test_bedrock.py`) to check that AWS credentials (via OIDC) and the Bedrock API call both worked, and a broken file (`insecure_test.py`) used to trigger the reviewer. These scripts were deleted once the workflow was confirmed working, and this branch was never merged into `main`. These are not needed in the final project.

### `test/performance-issue`
 
Adds `sample_app/performance_example.py`, a duplicate-finder function that compares every item in a list to every other item. The nested-loop approach gets a lot slower as the list increases, so it was used to check that the AI reviewer picks up on performance issues.

### `test/reliability-issue`
 
Adds `sample_app/reliability_example.py`, a function that opens a file with no error handling. If the file is missing or unreadable, the program crashes instead of failing gracefully. Used to check that the reviewer flags missing error handling.

### `test/security-issues`
 
Adds `sample_app/security_examples.py`, which contains a hardcoded (fake) API key and a SQL query built with string concatenation, a SQL injection risk. Used to check that the reviewer flags potential security issues.


