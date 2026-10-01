import requests

USERNAME = "Nath-Ramirez"

GRAPHQL_URL = "https://api.github.com/graphql"

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
          totalCount
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

    print(
        f'{repo["owner"]["login"]}/{repo["name"]}'
        f' → {item["contributions"]["totalCount"]} commits'
    )
