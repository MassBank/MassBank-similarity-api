FROM maven:3.9-eclipse-temurin-21
RUN apt-get update && apt-get install -y --no-install-recommends jq && rm -rf /var/lib/apt/lists/*

COPY generate.sh config-openapi.yaml openapi.yaml /usr/src/app/

WORKDIR /usr/src/app
RUN bash generate.sh

FROM python:3.13-slim-bookworm
WORKDIR /usr/src/app
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /usr/src/app/
RUN uv sync --locked --no-dev
ENV PATH="/usr/src/app/.venv/bin:$PATH"

COPY --from=0 /usr/src/app/openapi.yaml /usr/src/app/openapi.yaml
COPY --from=0 /usr/src/app/gen /usr/src/app/gen
COPY similarity_api_impl /usr/src/app/similarity_api_impl

EXPOSE 8080/tcp
ENTRYPOINT ["python", "-m", "similarity_api_impl"]