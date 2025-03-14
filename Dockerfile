FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
	# App dependencies
	gosu inotify-tools \
	# Troubleshooting tools
	vim htop curl \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install python packages
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
	--mount=type=cache,target=/root/.cache/uv \
	uv sync --locked --compile-bytecode --no-build --no-install-project

COPY src ./src

# Streamlit configuration
RUN mkdir -p .streamlit
COPY streamlit.toml .streamlit/config.toml

# Run the application
CMD [ "/app/src/entrypoint.sh" ]
