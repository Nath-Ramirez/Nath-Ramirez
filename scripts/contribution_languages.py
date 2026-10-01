import os
import requests
from datetime import datetime, timezone

USERNAME = "Nath-Ramirez"
GRAPHQL_URL = "https://api.github.com/graphql"

TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("Error: GITHUB_TOKEN no está configurado.")
    exit()


query = """
query(
    $login: String!,
    $from: DateTime!,
    $to: DateTime!,
    $after: String
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

                contributions(
                    first: 100
                    after: $after
                ) {

                    nodes {
                        commitCount
                        occurredAt
                    }

                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
    }
}
"""


# --------------------------------------------------
# PERÍODO QUE QUEREMOS CONSULTAR
# --------------------------------------------------

FROM_DATE = "2020-01-01T00:00:00Z"

TO_DATE = datetime.now(timezone.utc).strftime(
    "%Y-%m-%dT%H:%M:%SZ"
)


# --------------------------------------------------
# FUNCIÓN PARA HACER LA PETICIÓN
# --------------------------------------------------

def get_contributions(after=None):

    response = requests.post(
        GRAPHQL_URL,

        json={
            "query": query,

            "variables": {
                "login": USERNAME,
                "from": FROM_DATE,
                "to": TO_DATE,
                "after": after
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

    return data["data"]["user"]["contributionsCollection"]


# --------------------------------------------------
# OBTENER TODOS LOS REPOSITORIOS
# --------------------------------------------------

repositories = {}

cursor = None

while True:

    collection = get_contributions(cursor)

    for item in collection["commitContributionsByRepository"]:

        repo = item["repository"]

        repo_key = (
            f'{repo["owner"]["login"]}/{repo["name"]}'
        )

        if repo_key not in repositories:

            repositories[repo_key] = {
                "owner": repo["owner"]["login"],
                "name": repo["name"],
                "isFork": repo["isFork"],
                "isPrivate": repo["isPrivate"],
                "commits": 0,
                "dates": []
            }

        contributions = item["contributions"]

        for contribution in contributions["nodes"]:

            repositories[repo_key]["commits"] += (
                contribution["commitCount"]
            )

            repositories[repo_key]["dates"].append(
                contribution["occurredAt"]
            )

        page_info = contributions["pageInfo"]

        if page_info["hasNextPage"]:

            # Continuamos con la siguiente página
            cursor = page_info["endCursor"]

        else:

            break

    else:

        # Este else pertenece al for.
        # Si terminó normalmente, salimos del while.
        break


# --------------------------------------------------
# MOSTRAR INFORMACIÓN GENERAL
# --------------------------------------------------

print()
print("=" * 60)
print("CONTRIBUTIONS COLLECTION")
print("=" * 60)

print(
    f'Periodo: {collection["startedAt"]} → '
    f'{collection["endedAt"]}'
)

print(
    f'Total commits registrados: '
    f'{collection["totalCommitContributions"]}'
)

print(
    f'Repositorios con commits: '
    f'{collection["totalRepositoriesWithContributedCommits"]}'
)

print()


# --------------------------------------------------
# MOSTRAR REPOSITORIOS
# --------------------------------------------------

print("=" * 60)
print("REPOSITORIES")
print("=" * 60)

for repo_key, repo in repositories.items():

    dates = sorted(repo["dates"])

    first_date = dates[0] if dates else "N/A"
    last_date = dates[-1] if dates else "N/A"

    print()
    print(repo_key)

    print(
        f'  Commits: {repo["commits"]}'
    )

    print(
        f'  Primera contribución: {first_date}'
    )

    print(
        f'  Última contribución: {last_date}'
    )

    print(
        f'  Privado: {repo["isPrivate"]}'
    )

    print(
        f'  Fork: {repo["isFork"]}'
    )
