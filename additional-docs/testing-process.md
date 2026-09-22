# AI DevOps Code Reviewer - Testing Process

## Testing Objective
The goal of testing was to evaluate whether the AI reviewer could identify
deliberately introduced code issues in pull requests (PR). 

Three separate pull requests were created so each type of issue could be
tested independently.

## Test Environment

- GitHub Actions
- AWS Bedrock
- Claude Haiku 4.5
- Python 3.12
- GitHub OIDC authentication
- Base branch: `main`

Each test branch contained deliberately flawed code and was opened as a
pull request into `main`.

![Testing PR Creation](images/test-pr-creation-process)

---

# Test 1 – Security Issues
**Branch:** `test/security-issues`  
**PR:** PR #X

## Planted Issues
1. Hard-coded API key
2. SQL query constructed using string concatenation

## Expected Result
The reviewer should identify:
- exposed credentials
- possible SQL injection

![Test 1 - Security Issue Planted In sample_app](images/test-1-security-review)
![Test 1 - Security Issue Planted In sample_app](images/test-1-additional-findings)
  
---

# Test 2 – Reliability Issue Detection

**Branch:** `test/reliability-issue`  
**Pull Request:** #3

## Planted Issue
1. File being opened without handling possible exceptions

## Expected Result
The reviewer should identify: 
- invalid or inaccessible file paths
- Missing file operation error handling
- Recommend using try-except blocks or clearly documenting
- Recommend that caller must handle exceptions

![Test 2 - Reliability Issue Planted In sample_app](images/test-2-reliability-issue)

---

# Test 3 – Performance Issue Detection

**Branch:** `test/performance-issue`  
**Pull Request:** #4

## Planted Issue
1. Nested loop resulting in O(n^2) complexity
2. Performance degradation as input size increases

## Expected Result
The reviewer should identify: 
- the O(n²) nested-loop implementation
- The potential performance impact for large inputs
- A more efficient approach using a set or dictionary

![Test 3 - Performance Issue Planted In sample_app](images/test-3-performance-issue)

