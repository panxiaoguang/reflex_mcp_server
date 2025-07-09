# reflex_mcp_server

## how to implement mcp server

1. download reflex [docs](https://github.com/reflex-dev/reflex-web/tree/main/docs) from [reflex-web](https://github.com/reflex-dev/reflex-web) repo.
2. run `python populate_db.py` to create and import the data into the database
3. use fastapi to create some endpoints to get the data from the database
4. use fastapi_mcp to create the mcp server
5. deploy the mcp server to tadata

## how to run

install the dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

run the fastapi server

```bash
fastapi run
```

the sse mcp will be available at `http://localhost:8000/mcp`
