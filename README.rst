
Create venv:
    $ virtualenv -p python3 vdef
    $ vdef/bin/pip install -e path/to/code
    $ vdef/bin/python -m aiohttp.web -H localhost -P 8080 defiler.server:init
