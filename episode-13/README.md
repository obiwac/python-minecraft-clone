# Episode 13

This episode is split into two parts:

- EP13a: General cleanup.
- EP13b: Performance improvements (both in terms of loading time and frame time).

## Installing dependencies

Using [Poetry](https://python-poetry.org/):

```console
poetry install
```

This will also build the Cython extensions.
If you ever need to re-build them, you can do:

```console
poetry build
```

## Running

Again, using Poetry:

```console
poetry run python mcpy.py
```
