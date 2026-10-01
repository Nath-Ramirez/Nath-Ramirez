import os
import requests
from datetime import datetime, timezone, timedelta

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
query(
    $login: String!,
    $from: DateTime!,
    $to: DateTime!
) {
    user(login: $login) {
        contributionsCollection(
            from: $from
            to: $to
        ) {
            startedAt
            endedAt
            totalCommitContributions
            totalRepositoriesWithContributedCommits

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

                    pageInfo {
                        hasNextPage
                    }
                }
            }
        }
    }
}
"""


def get_contributions(from_date, to_date):

    variables = {
        "login": USERNAME,
        "from": from_date,
        "to": to_date
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


# --------------------------------------------------
# Buscar todo el historial en bloques de 3 meses
# --------------------------------------------------

START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime.now(timezone.utc)

repositories = {}

current_start = START_DATE

while current_start < END_DATE:

    # Aproximadamente 3 meses
    current_end = current_start + timedelta(days=90)

    if current_end > END_DATE:
        current_end = END_DATE

    from_date = current_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_date = current_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\nConsultando: {from_date} → {to_date}")

    collection = get_contributions(from_date, to_date)

    print(
        f"  Commits registrados: "
        f"{collection['totalCommitContributions']}"
    )

    print(
        f"  Repositorios: "
        f"{collection['totalRepositoriesWithContributedCommits']}"
    )

    for item in collection["commitContributionsByRepository"]:
    
        repo = item["repository"]

        if repo["isPrivate"]:
            continue
        
        if repo["isFork"]:
            continue
        
        if repo["owner"].lower() == USERNAME.lower():
            continue

        owner = repo["owner"]["login"]
        name = repo["name"]

        full_name = f"{owner}/{name}"

        if full_name not in repositories:
            repositories[full_name] = {
                "owner": owner,
                "name": name,
                "commits": 0,
                "dates": [],
                "isPrivate": repo["isPrivate"],
                "isFork": repo["isFork"]
            }

        repo_data = repositories[full_name]

        contributions = item["contributions"]

        for contribution in contributions["nodes"]:

            repo_data["commits"] += contribution["commitCount"]

            repo_data["dates"].append(
                contribution["occurredAt"]
            )

        if contributions["pageInfo"]["hasNextPage"]:
            print(
                f"  WARNING: {full_name} tiene más de "
                f"100 días de contribuciones en este período."
            )

    current_start = current_end


# --------------------------------------------------
# Mostrar resultados
# --------------------------------------------------

print("\n")
print("=" * 60)
print("CONTRIBUTIONS COLLECTION")
print("=" * 60)

print(f"Usuario: {USERNAME}")
print(f"Periodo: {START_DATE.date()} → {END_DATE.date()}")

print("\n")
print("=" * 60)
print("REPOSITORIES")
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
    print(f"  Privado: {repo['isPrivate']}")
    print(f"  Fork: {repo['isFork']}")
