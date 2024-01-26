# MyAnimeStats

See statistics about lists from [MyAnimeList](https://myanimelist.net/).

TODO logo and images

## Setup

### Clone the repository

```sh
git clone https://github.com/titouanlacombe/myanimestats.git
```

### Install the virtual python environment

using pipenv ([Install pipenv](https://github.com/pypa/pipenv?tab=readme-ov-file#installation)):

```sh
pipenv install
```

### Configuration

Before the next steps, copy the `.env.example` file to `.env`, you will use this file to configure the project.

### Jikan API

The project can use the [official Jikan API](https://jikan.moe/) or self-host it using docker.

If you use the official Jikan API, you will be limited to 1 request per second (~1 anime per second).

If you self-host it, you need to have [docker](https://docs.docker.com/get-docker/) installed.

#### Using the official Jikan API

You don't need to do anything, the project will use the official Jikan API by default.

#### Self-hosting Jikan

With docker installed, in `.env`, change `SELF_HOST_JIKAN` to `true`.

Optionally you can change the `JIKAN_PORT` variable to the port you want to use.

Then, just run the following command to start the local Jikan API:

```sh
make up
```

Jikan will be available at `http://localhost:{JIKAN_PORT}/v4`, the project will use this URL to make requests.

### Run the notebook

Run the notebooks in the pipenv environment with the method of your choice (e.g. VSCode, Jupyter, ...).

For example, you can run the web server notebook using the following command:

```sh
make notebook
```

## Usage

The notebook will ask you for your MyAnimeList username to scrap your list.

You can save your username in `data/username.txt` to avoid having to enter it every time.

If you want to scrape your list, make sure it is public, you can make your list public [here](https://myanimelist.net/editprofile.php?go=listpreferences)

Alternatively, if you want your list to stay private, you can export you MyAnimeList data from [here](https://myanimelist.net/panel.php?go=export) and save it to `data/animelist.xml.gz`.

Now you can run all the cells in the notebook and see the results.

## Results

For example, here are the stats of popular YouTuber [Gigguk](https://www.youtube.com/user/gigguk) (MAL username `gigguk`):

TODO
