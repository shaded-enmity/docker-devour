# docker-devour
Consume Docker API's in a sensible way - this set of scripts let you generate Docker API bindings for your favorite language. 
Python templates are bundled by default (+JSON for remote api).

## Scope
- Docker-CLI
  - Extract Docker commands like run, build, commit, pull ...
  - Extract all --/- flag information for the commands

- Docker Remote API
  - Extract all REST requests

- Docker Registry API
  - Extract all REST requests

## Implementation
The Docker-CLI part is implemented in `extract-flags.sh`, `extract-verbs.sh` and `python-bindings.sh` in fairly straightfoward 40 lines of code.

The Remote/Registry API is much more complicated as there's no well-formatted source of information, see `api_parser.py`, so here we rely on parsing the HTML with Python + BeautifulSoup.

In the file `docker_api.py` you can find the definition of the base classes that are further used by the rest of the tools. 

## Configuration
Output of `api_parser.py` is templatized upon parsing, so see the attached template files for more information. `api_parser.py --help` also might help you.

## Example
```bash
# let's parse Docker Remote API v1.16
curl https://docs.docker.com/reference/api/docker_remote_api_v1.16/ | ./api_parser.py -

# or Registry API ...
curl https://docs.docker.com/reference/api/registry_api/ | ./api_parser.py -

# dump CLI flags in Python format
./python-bindings.sh
```

## License
GPLv3

