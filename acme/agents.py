"""Loader for the agent definitions in agents/*.toml.

Each file is one agent in our own simple format. The loader only reads and
validates the shape; the tests check the contents against servers and routing.
"""

import tomllib
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
REQUIRED_KEYS = {"name", "description", "skills", "tools", "delegates", "system_message"}


def load_agents(directory: Path = AGENTS_DIR) -> dict[str, dict]:
    """Read every agents/*.toml with tomllib, keyed by name.
    Raise ValueError naming the file if a key is missing or name != file stem."""
    agents = {}
    for path in sorted(Path(directory).glob("*.toml")):
        with path.open("rb") as handle:
            agent = tomllib.load(handle)
        missing = REQUIRED_KEYS - set(agent)
        if missing:
            raise ValueError(f"{path.name}: missing keys {sorted(missing)}")
        if agent["name"] != path.stem:
            raise ValueError(f"{path.name}: name {agent['name']!r} does not match file name {path.stem!r}")
        agents[agent["name"]] = agent
    return agents
