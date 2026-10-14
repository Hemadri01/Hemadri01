"""Fetch public repositories pinned on a GitHub profile."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
GRAPHQL_URL = "https://api.github.com/graphql"
QUERY = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: [REPOSITORY]) {
      nodes {
        ... on Repository {
          nameWithOwner
          url
          description
        }
      }
    }
  }
}
"""


def parse_pinned_response(payload: dict) -> list[dict[str, str]]:
    """Keep only the repository details needed by the generic README renderer."""
    if payload.get("errors"):
        raise ValueError(f"GitHub GraphQL error: {payload['errors']}")
    user = payload.get("data", {}).get("user")
    if user is None:
        raise ValueError("GitHub did not return the requested user")
    nodes = user["pinnedItems"]["nodes"]
    repositories = []
    for node in nodes:
        if not node:
            continue
        repositories.append({
            "name": node["nameWithOwner"],
            "summary": " ".join((node.get("description") or "").split()),
            "url": node["url"],
        })
    return repositories


def fetch_pinned(username: str, token: str) -> list[dict[str, str]]:
    request = Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "github-profile-readme-generator",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    return parse_pinned_response(payload)


def main(root: Path = ROOT) -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GH_TOKEN to a token that can query the GitHub GraphQL API")
    profile = json.loads((root / "data/profile.json").read_text(encoding="utf-8"))
    repositories = fetch_pinned(profile["username"], token)
    output = root / "data/pinned_repos.json"
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if (isinstance(previous, dict)
                and previous.get("username") == profile["username"]
                and previous.get("source") == "github-graphql"
                and previous.get("repositories") == repositories):
            print(f"Pinned repositories unchanged for {profile['username']}")
            return
    snapshot = {
        "username": profile["username"],
        "source": "github-graphql",
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repositories": repositories,
    }
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Fetched {len(repositories)} pinned repositories for {profile['username']}")


if __name__ == "__main__":
    main()
