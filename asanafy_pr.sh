#!/usr/bin/env bash
#
# asanafy_pr.sh
#
# Usage: asanafy_pr.sh [GITHUB_PR_URL]
#
# Creates an Asana subtask to code review a GitHub PR. Looks for an Asana task
# link in the PR description, makes a subtask of that task named 'review PR' with
# the PR URL in the description. Assigns the task if the review is assigned to a
# GitHub user and a matching Asana user is found.
#
# Fill in the USERS constant before running!
#
# Requires coreutils (for gdate), jq, curl.
# Install on Mac with:
#   brew install coreutils jq
#
# Install on Linux with:
# sudo apt update && sudo apt install jq && sudo ln -s $(which date) /bin/gdate
#
# Requires Asana and GitHub API tokens in the ASANA_TOKEN and GITHUB_TOKEN
# environment variables. The GitHub token needs `repo` scope. You can get
# tokens from:
#   https://app.asana.com/0/developer-console
#   https://github.com/settings/tokens
#
# Asana API docs: https://developers.asana.com/docs/errors
# GitHub GraphQL API docs: https://docs.github.com/en/graphql/

# Exit on first error, unset variable, or pipe failure
set -euo pipefail
# set -x

# Set these in environment variables.
# ASANA_TOKEN=...
# GITHUB_TOKEN=...

# JSON mapping GitHub username to Asana user id.
#
# Our GitHub usernames are here:
#   https://github.com/orgs/[NAME]/people
#
# Use this to get all of your Asana users and ids:
#   curl -v https://app.asana.com/api/1.0/workspaces/[ID]/users -H "Authorization: Bearer $ASANA_TOKEN" | json_pp
USERS='{
  "foo": "123",
  ...
}'

# Read GitHub URL with fallback to empty string (skips `set -u`)
github_url="${1:-}"
if [[ $# != 1 || ! "$github_url" =~ ^https://github\.com/[^/]+/[^/]+/pull/[0-9]+/?$ ]]; then
  echo "Usage: asanafy_pr.sh [GITHUB_PR_URL]" 1>&2
  exit 1
fi

#
# extract Asana task id from GitHub PR
# https://docs.github.com/en/graphql/reference/unions#issueorpullrequest
#
path="$(echo "$github_url" | sed -E 's/^https:\/\/github\.com\///')"
owner="$(echo "$path" | cut -d/ -f1)"
repo="$(echo "$path" | cut -d/ -f2)"
number="$(echo "$path" | cut -d/ -f4)"

pr="$(curl -H "Authorization: bearer ${GITHUB_TOKEN}" https://api.github.com/graphql -d @- <<EOF
{
  "query": "query {
    repository(owner: \"${owner}\", name: \"${repo}\") {
      issueOrPullRequest(number: ${number}) {
        ... on PullRequest {
          id
          title
          body
          reviewRequests(first: 1) {
            nodes {
              requestedReviewer {
                ... on User { login }
              }
            }
          }
        }
      }
    }
  }"
}
EOF
)"

# GraphQL always returns HTTP 200 and reports errors in the body
# jq will output errors to stderr, the if fails due to non-zero exit code
if echo "$pr" | jq -e .errors; then
  echo '(from GitHub API)' 1>&2
  exit 1
fi

#
# create Asana subtask
# https://developers.asana.com/docs/create-a-subtask
#
task_id="$(echo "$pr" | jq -r .data.repository.issueOrPullRequest.body \
  | grep -o -E 'https://app.asana.com/0/[^ )]+' \
  | tail -n 1 \
  | sed -E 's/https:\/\/app.asana.com\/0\/[^/]+\/([^/]+).*/\1/')"
if [[ "$task_id" == "" ]]; then
  echo 'GitHub PR has no Asana link!' 1>&2
  exit 1
fi

reviewer="$(echo "$pr" | jq -r .data.repository.issueOrPullRequest.reviewRequests.nodes[0].requestedReviewer.login)"
if [[ "$reviewer" == "null" ]]; then
  echo 'GitHub PR has no reviewer assigned!' 1>&2
  exit 1
fi
assignee=$(echo "$USERS" | jq -r ."$reviewer")

subtask="$(curl https://app.asana.com/api/1.0/tasks/${task_id}/subtasks \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H "Authorization: Bearer ${ASANA_TOKEN}" \
  -d @- <<EOF
{
  "data": {
    "name": "review PR",
    "notes": "$1",
    "due_on": "$(gdate -d tomorrow -Idate)",
    "assignee": "$assignee"
  }
}
EOF
)"

if echo "$subtask" | jq -e .errors; then
  echo '(from Asana API)' 1>&2
  exit 1
fi

echo "$subtask" | jq -r .data.permalink_url
