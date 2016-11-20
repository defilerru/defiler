
Create venv:
    $ cd defiler
    $ virtualenv -p python3 .venv
    $ .venv/bin/pip install -e .
    $ .venv/bin/python -m aiohttp.web -H localhost -P 8080 defiler.server:init
