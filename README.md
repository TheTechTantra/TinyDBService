# TinyDBService

A minimal FastAPI service that stores key/value credentials in a [TinyDB](https://tinydb.readthedocs.io/) JSON file.

> ⚠️ **Security note:** This service has **no authentication** and stores values in **plaintext**. Do **not** expose it to the public internet. Run it only on localhost or behind a private Docker network / firewall.

## Setup (local)

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip3 install -r requirements.txt
```

## Run the server

```bash
uvicorn app:app --host 0.0.0.0 --port 28080
```

## Run with Docker

Build the image:

```bash
docker build -t tinydb-service .
```

Run it, mounting a host file for persistence (replace `/path/to/db.json` with your own local path):

```bash
docker run -v /path/to/db.json:/app/db.json -p 28080:28080 tinydb-service
```

Run it on a private Docker network (replace `<network-name>` with your own):

```bash
docker run --net <network-name> --name tinydbservice \
  -v /path/to/db.json:/app/db.json -p 28080:28080 tinydb-service
```

## API

| Method | Path                | Description                |
|--------|---------------------|----------------------------|
| GET    | `/credential/{key}` | Read a value by key        |
| POST   | `/key/`             | Store a `{key, value}` pair |
| DELETE | `/key/{key}`        | Delete a value by key      |
