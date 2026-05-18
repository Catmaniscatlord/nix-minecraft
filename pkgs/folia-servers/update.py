#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3Packages.requests

import base64
import json
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

# The Fill v3 API. Folia, Paper, Velocity and Waterfall are all served here.
# Full docs: https://fill.papermc.io/swagger-ui/index.html
ENDPOINT = "https://fill.papermc.io/v3"
PROJECT = "folia"

# Which download artifact to lock. Folia and Paper publish "server:default".
DOWNLOAD_KEY = "server:default"

session = requests.Session()


def get(*path):
    """GET a Fill v3 project endpoint and return the decoded JSON body."""
    url = "/".join((ENDPOINT, "projects", PROJECT) + path)
    response = session.get(url)
    response.raise_for_status()
    return response.json()


def get_game_versions():
    """
    Return the list of Minecraft versions supported by the project, filtered
    each group's list is ordered newest-first.
    """
    data = get()
    versions = [v for group in data["versions"].values() for v in group]
    return versions


def get_latest_build(game_version):
    builds = get("versions", game_version, "builds?channel=STABLE")

    if len(builds) == 0:
        return None
    # The builds endpoint returns an array ordered newest-first
    return builds[0]


def gen_lock(build):
    download = build["downloads"][DOWNLOAD_KEY]
    return {
        build["id"]: {
            "url": download["url"],
            "sha256": download["checksums"]["sha256"],
        }
    }


def main(lock):
    output = {}
    game_versions = get_game_versions()

    for game_version in game_versions:
        build = get_latest_build(game_version)
        if build is not None:
            output[game_version] = gen_lock(build)

    json.dump(output, lock, indent=2)


if __name__ == "__main__":
    folder = Path(__file__).parent
    lo = folder / "lock.json"
    main(open(lo, "w"))
