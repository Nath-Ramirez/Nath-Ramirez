import os
import requests

USERNAME = "Nath-Ramirez"
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("ERROR: GITHUB_TOKEN no está configurado.")
    exit()

URL = "https://api.github.com/graphql"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}

QUERY = """
query($login: String!) {
    user(login: $login) {
        contributionsCollection {
            commitContributionsByRepository(
                maxRepositories: 100
            ) {
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


def get_contributions():

    variables = {
        "login": USERNAME
    }

    response = requests.post(
        URL,
        json={
            "query": QUERY,
            "variables": variables
        },
        headers=HEADERS
    )

    data = response.json()

    if "errors" in data:
        print("GraphQL errors:")

        for error in data["errors"]:
            print(error["message"])

        exit()

    return data["data"]["user"]["contributionsCollection"]


def get_languages(owner, repo):

    url = f"https://api.github.com/repos/{owner}/{repo}/languages"

    response = requests.get(
        url,
        headers=HEADERS
    )

    if response.status_code != 200:
        print(
            f"Error obteniendo lenguajes de "
            f"{owner}/{repo}: {response.status_code}"
        )
        return {}

    return response.json()
    

# --------------------------------------------------
# Obtener contribuciones
# --------------------------------------------------

collection = get_contributions()

repositories = {}

for item in collection["commitContributionsByRepository"]:

    repo = item["repository"]

    owner = repo["owner"]["login"]
    name = repo["name"]

    # Ignorar repositorios privados
    if repo["isPrivate"]:
        continue

    # Ignorar forks
    if repo["isFork"]:
        continue

    # Ignorar nuestros propios repositorios
    if owner.lower() == USERNAME.lower():
        continue

    full_name = f"{owner}/{name}"

    if full_name not in repositories:

        repositories[full_name] = {
            "owner": owner,
            "name": name,
            "commits": 0,
            "dates": []
        }

    repo_data = repositories[full_name]

    for contribution in item["contributions"]["nodes"]:

        repo_data["commits"] += contribution["commitCount"]

        repo_data["dates"].append(
            contribution["occurredAt"]
        )


# --------------------------------------------------
# Mostrar resultados
# --------------------------------------------------

print("\n")
print("=" * 60)
print("EXTERNAL REPOSITORIES")
print("=" * 60)

for full_name, repo in sorted(
    repositories.items(),
    key=lambda item: item[1]["commits"],
    reverse=True
):

    dates = repo["dates"]

    first_date = min(dates) if dates else "N/A"
    last_date = max(dates) if dates else "N/A"

    print(f"\n{full_name}")
    print(f"  Commits: {repo['commits']}")
    print(f"  Primera contribución: {first_date}")
    print(f"  Última contribución: {last_date}")
