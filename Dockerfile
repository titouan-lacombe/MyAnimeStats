FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
	pipenv inotify-tools \
	# Install troubleshooting tools
	vim htop curl \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install python packages
COPY Pipfile Pipfile.lock ./
RUN pipenv sync -v --system --clear && pipenv --clear

# Copy the current directory contents into the container at /app
COPY src ./src

# Streamlit configuration
RUN mkdir -p .streamlit
COPY streamlit.toml .streamlit/config.toml

# Run the application
CMD [ "streamlit", "run", "src/MyAnimeStats.py" ]
