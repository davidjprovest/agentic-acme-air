# Agentic Acme Air

The pure-Python core of the Acme Air multi-agent lab: synthetic airline data, 8 tools, 5 MCP servers, a deterministic reviewer and a routing baseline. Acme Air is fictional.

## Quickstart

```bash
uv sync
uv run pytest -q
```

Poke at a server by hand in the MCP Inspector (start servers as modules, never `mcp dev <file>`):

```bash
npx @modelcontextprotocol/inspector uv run python -m servers.fares_server
```

Run the live LLM-router comparison (needs Ollama running with `qwen3.5:9b`):

```bash
ACME_LLM=1 uv run pytest -m llm -s -q
```

## Read next

- [docs/TUTORIAL.md](docs/TUTORIAL.md): one chapter per build step, with the ideas behind each
- [TECH_STACK.md](TECH_STACK.md): what the project runs on
- [tonight/](tonight/): chunk 01 plan and build spec
- [plans/](plans/): later chunks
- [Lab specification](Acme%20Air%20multi-agent%20lab%20open%20source%20specification.md)
