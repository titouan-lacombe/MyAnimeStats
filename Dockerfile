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
RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv sync -v --system --clear && pip cache purge

COPY src ./src

# Streamlit configuration
RUN mkdir -p .streamlit
COPY streamlit.toml .streamlit/config.toml

# Run the application
CMD [ "/app/src/entrypoint.sh" ]
