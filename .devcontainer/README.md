# MassBank-similarity-api Dev Container

The development container uses Ubuntu 26.04, uv-managed Python 3.13 (matching CI), and Java/Maven for OpenAPI code generation. On creation, it syncs `.venv` from `uv.lock` and generates the API code.

## Container configuration

The configuration targets rootless Podman: it keeps the host workspace path, uses `:Z` for SELinux labeling, and maps the host user to `vscode` (1000/1000). Automatic UID rewriting is disabled. The named volumes `codex-devcontainer` and `copilot-devcontainer` persist agent state across container rebuilds.

The Python interpreter is located at `.venv/bin/python` inside the workspace.

## Run and test

Start the API from the repository root:

```bash
uv run python -m similarity_api_impl
```

Port 8080 is forwarded by the container. Run the test suite with:

```bash
uv run python -m unittest discover -s test
```

## Updating dependencies

After changing dependencies in `pyproject.toml`, update the lockfile and environment:

```bash
uv lock
uv sync
```

Rebuild the Dev Container after changing the Dockerfile.
