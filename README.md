# MyAnimeStats

Analyse your anime stats from MyAnimeList.net

## Usage

Export you MyAnimeList data from [here](https://myanimelist.net/panel.php?go=export).

Install the virtual environment using pipenv:

```sh
pipenv install
```

If you don't have pipenv, you can install it with pip:

```sh
pip install pipenv
```

Then run the notebooks in the environment.

For example, to run the web notebook:
```sh
pipenv run jupyter notebook
```

Notebooks files:

- import.ipynb imports your data and completes it with data from the [Jikan API](https://jikan.moe/).
- franchises.ipynb regroups your anime by franchise.
- stats.ipynb displays stats about your franchises.

So in most use cases, just run: import -> franchises -> stats
