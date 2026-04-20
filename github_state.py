import logging
import os

import requests

logger = logging.getLogger("github_state")


def update_github_variable(variable_name: str, value: str) -> None:
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    environment = os.environ.get('GITHUB_ENVIRONMENT')

    if not token or not repo or not environment:
        logger.warning(
            "GH_TOKEN, GITHUB_REPOSITORY o GITHUB_ENVIRONMENT non impostati: "
            "lo stato non verrà persistito su GitHub Variables."
        )
        return

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    base_url = f"https://api.github.com/repos/{repo}/environments/{environment}/variables"

    response = requests.patch(f"{base_url}/{variable_name}", headers=headers, json={"name": variable_name, "value": value})
    if response.status_code == 204:
        logger.debug(f"Variabile {variable_name} aggiornata.")
        return

    if response.status_code == 404:
        response = requests.post(base_url, headers=headers, json={"name": variable_name, "value": value})
        if response.status_code == 201:
            logger.debug(f"Variabile {variable_name} creata.")
            return

    logger.warning(
        f"Impossibile aggiornare variabile {variable_name}: "
        f"{response.status_code} {response.text}"
    )
