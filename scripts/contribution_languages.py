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
    

def generate_svg(languages, output_file="dist/contribution-languages.svg"):

    width = 900
    height = 320

    background = "#0D1117"
    cyan = "#8CE3FF"
    text_color = "#FFFFFF"
    muted = "#9CA3AF"

    language_colors = {
        "JavaScript": "#8CE3FF",
        "Python": "#C7A6FF",
        "TypeScript": "#6E9CFF",
        "CSS": "#B58CFF",
        "HTML": "#5BC0EB",
    }

    total_bytes = sum(languages.values())

    if total_bytes == 0:
        print("No hay lenguajes para generar el SVG.")
        return

    # Ordenar de mayor a menor
    sorted_languages = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # --------------------------------------------------
    # SVG
    # --------------------------------------------------

    svg = f'''<svg
        xmlns="http://www.w3.org/2000/svg"
        width="{width}"
        height="{height}"
        viewBox="0 0 {width} {height}">

        <rect
            width="100%"
            height="100%"
            rx="16"
            fill="{background}"/>

        <text
            x="40"
            y="45"
            fill="{cyan}"
            font-family="monospace"
            font-size="22"
            font-weight="bold">
            CONTRIBUTION LANGUAGES
        </text>

        <text
            x="40"
            y="70"
            fill="{muted}"
            font-family="monospace"
            font-size="12">
            PUBLIC REPOSITORIES I CONTRIBUTED TO
        </text>
    '''

    # --------------------------------------------------
    # Donut
    # --------------------------------------------------

    cx = 200
    cy = 185
    radius = 80
    stroke_width = 28

    circumference = 2 * 3.14159265359 * radius

    offset = 0

    for language, bytes_count in sorted_languages:

        percentage = bytes_count / total_bytes
        dash_length = percentage * circumference

        color = language_colors.get(language, "#A78BFA")

        svg += f'''
        <circle
            cx="{cx}"
            cy="{cy}"
            r="{radius}"
            fill="none"
            stroke="{color}"
            stroke-width="{stroke_width}"
            stroke-dasharray="{dash_length} {circumference - dash_length}"
            stroke-dashoffset="{-offset}"
            transform="rotate(-90 {cx} {cy})"/>
        '''

        offset += dash_length

    # Texto central

    svg += f'''
        <text
            x="{cx}"
            y="{cy - 4}"
            text-anchor="middle"
            fill="{text_color}"
            font-family="monospace"
            font-size="20"
            font-weight="bold">
            {len(sorted_languages)}
        </text>

        <text
            x="{cx}"
            y="{cy + 18}"
            text-anchor="middle"
            fill="{muted}"
            font-family="monospace"
            font-size="11">
            LANGUAGES
        </text>
    '''

    # --------------------------------------------------
    # Lista de lenguajes
    # --------------------------------------------------

    start_x = 360
    start_y = 120
    line_height = 36

    for index, (language, bytes_count) in enumerate(sorted_languages):

        percentage = bytes_count / total_bytes * 100

        color = language_colors.get(language, "#A78BFA")

        y = start_y + index * line_height

        svg += f'''
        <circle
            cx="{start_x}"
            cy="{y - 5}"
            r="5"
            fill="{color}"/>

        <text
            x="{start_x + 16}"
            y="{y}"
            fill="{text_color}"
            font-family="monospace"
            font-size="14">
            {language}
        </text>

        <text
            x="820"
            y="{y}"
            text-anchor="end"
            fill="{color}"
            font-family="monospace"
            font-size="14"
            font-weight="bold">
            {percentage:.2f}%
        </text>
        '''

    svg += "</svg>"

    os.makedirs(
    os.path.dirname(output_file),
    exist_ok=True
    )
    
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(svg)

    print(f"\nSVG generado correctamente: {output_file}")
    
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

all_languages = {}

for full_name, repo in sorted(
    repositories.items(),
    key=lambda item: item[1]["commits"],
    reverse=True
):

    owner = repo["owner"]
    name = repo["name"]

    print(f"\n{full_name}")
    print(f"  Commits: {repo['commits']}")

    languages = get_languages(owner, name)

    print("  Languages:")

    for language, bytes_count in languages.items():

        print(
            f"    {language}: "
            f"{bytes_count:,} bytes"
        )

        if language not in all_languages:
            all_languages[language] = 0

        all_languages[language] += bytes_count


print("\n")
print("=" * 60)
print("LANGUAGES")
print("=" * 60)

total_bytes = sum(all_languages.values())

for language, bytes_count in sorted(
    all_languages.items(),
    key=lambda item: item[1],
    reverse=True
):

    percentage = (
        bytes_count / total_bytes * 100
        if total_bytes > 0
        else 0
    )

    print(
        f"{language}: "
        f"{percentage:.2f}%"
    )

generate_svg(all_languages)
