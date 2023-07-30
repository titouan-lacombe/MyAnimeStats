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

Then run the notebook you want in the virtual environment.

For example, to run the web notebook:
```sh
pipenv run jupyter notebook
```

import.ipynb imports your data and completes it with data from the [Jikan API](https://jikan.moe/).

franchises.ipynb regroups your anime by franchise.

stats.ipynb displays some stats about your franchises.
