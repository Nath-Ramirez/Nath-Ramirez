import os
import requests

USERNAME = "Nath-Ramirez"

GRAPHQL_URL = "https://api.github.com/graphql"

TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("Error: GITHUB_TOKEN no está configurado.")
    exit()

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      commitContributionsByRepository(maxRepositories: 100) {
        repository {
          name
          owner {
            login
          }
          isFork
          isPrivate
        }

        contributions(first: 100) {
          nodes {
            commitCount
            occurredAt
          }
        }
      }
    }
  }
}
"""

response = requests.post(
    GRAPHQL_URL,
    json={
        "query": query,
        "variables": {
            "login": USERNAME
        }
    },
    headers={
        "Authorization": f"Bearer {TOKEN}"
    }
)

if response.status_code != 200:
    print("Error:", response.status_code)
    print(response.text)
    exit()

data = response.json()

if "errors" in data:
    print("GraphQL errors:")

    for error in data["errors"]:
        print(error["message"])

    exit()

repositories = (
    data["data"]
    ["user"]
    ["contributionsCollection"]
    ["commitContributionsByRepository"]
)

for item in repositories:

    repo = item["repository"]

    if repo["isPrivate"]:
        continue

    if repo["isFork"]:
        continue

    contributions = item["contributions"]["nodes"]

    total_commits = sum(
        contribution["commitCount"]
        for contribution in contributions
    )

    print(
        f'{repo["owner"]["login"]}/{repo["name"]}'
        f' → {total_commits} commits'
    )
