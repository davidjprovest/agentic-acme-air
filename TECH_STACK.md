# Tech Stack

What the project actually runs on. Exact package versions are pinned in `uv.lock`.

## Development

| Component | Purpose | Details |
|-----------|---------|---------|
| **VS Code** | IDE | Primary development environment |
| **uv** | Package and environment manager | `uv sync` installs from `uv.lock`; `uv run` runs inside the project venv |
| **Python 3.12** | Language | Pinned in `.python-version` (`requires-python = ">=3.12,<3.14"`) |
| **pytest 9** | Tests | `uv run pytest -q`; live LLM test is opt-in with `ACME_LLM=1` |

## Tools and agents

| Component | Purpose | Details |
|-----------|---------|---------|
| **`mcp` 1.30 (FastMCP)** | MCP servers | Five servers in `servers/`, started with `uv run python -m servers.<name>` |
| **MCP Inspector** | Manual server testing | `npx @modelcontextprotocol/inspector uv run python -m servers.fares_server` |

## AI and LLM runtime

| Component | Purpose | Details |
|-----------|---------|---------|
| **Ollama 0.40** | Local model runtime | HTTP API at `localhost:11434`, called with the standard library (no SDK) |
| **qwen3.5:9b** | Model | LLM router experiment in `acme/llm_router.py`. No structured-output support on Ollama 0.40, so JSON is parsed from free text |

Not installed yet: kagent, Kubernetes, the gateway and Keycloak. Later chunks add them.
