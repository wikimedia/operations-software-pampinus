Django-based dashboard to visualize database backups status, progress and failures.

## Dependencies

Some dependencies are required in order to run the scripts and the tests. The easiest way to work is by using a virtualenv:

```
tox --notest
tox -e venv -- <some command>
```

## Code style compliance

To check the code style compliance:

```
tox -e flake8
```

