# Fresh Onions TOR Hidden Service Crawler

This is a fork of the source for the http://zlal32teyptf4tvi.onion hidden service, which implements a tor hidden service crawler / spider and web site.

---

## Quick Start (Docker)

### Requirements
- Docker + Docker Compose

### 1. Build and start

```bash
docker-compose up --build -d
```

### 2. Verify everything is running

```bash
docker-compose ps
```

All services should be `Up`: `db`, `proxy`, `memcached`, `elastic`, `scrapy`, `isup`, `frontend`, `adminer`, `kibana`.

- Frontend: http://localhost:5000
- Adminer (DB UI): http://localhost:8080
- Elasticsearch: http://localhost:9200

### 3. Bulk-import onion addresses from Ahmia

The scraper starts with an empty DB. Pre-populate it with ~19k known v3 onion addresses from Ahmia:

```bash
# Copy the bulk insert script into the container
docker cp scripts/bulk_insert_domains.py freshonions-torscraper-scrapy-1:/tmp/bulk_insert.py

# Fetch Ahmia list and insert all domains
docker-compose exec scrapy sh -c "curl -skL 'https://ahmia.fi/onions/' | grep -E -o '[a-z2-7]{56}\.onion' | sort -u > /tmp/o.txt && python3 /tmp/bulk_insert.py"
```

Verify the count:
```bash
docker-compose exec db mysql -uroot -p8SLK3Bny tor -e "SELECT COUNT(*) FROM domain;"
```

### 4. Run harvest (optional, finds more onions from multiple sources)

```bash
docker-compose exec scrapy sh scripts/harvest.sh
```

### 5. Monitor crawling progress

```bash
# Count domains up vs total
docker-compose exec db mysql -uroot -p8SLK3Bny tor -e "SELECT COUNT(*) as total, SUM(is_up) as up FROM domain;"

# Live logs
docker-compose logs -f scrapy
```

### Stopping and wiping everything

```bash
# Stop and remove containers, volumes (DB data), and images
docker-compose down -v --rmi all
```

---

## Changes (2026-03-16)

### Onion v3 support / v2 removal
- Dropped onion v2 address support (16-char); crawler now validates **v3 only** (56-char base32 `a-z2-7`)
- `Domain.is_onion_url()` regex updated: `^([a-z0-9-]{1,63}\.)*[a-z2-7]{56}\.onion$`
- `Domain.random()` generates valid 56-char v3 addresses
- Fallback seed URLs replaced: old v2 directory links swapped for Torch v3 (`torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion`)
- Hardcoded v2 self-site exclusion (`zlal32teyptf4tvi.onion`) replaced with `SITE_ONION` env var — set this to your own instance's onion hostname to prevent self-crawling
- Cleared `spider_exclude` and `ALLOW_BIG_DOWNLOAD` lists (contained defunct v2 addresses)

### Dependencies
- `pycrypto` replaced with `pycryptodome==3.20.0` (pycrypto is abandoned and broken on modern Python)
- `elasticsearch` / `elasticsearch-dsl` pinned to `>=7.0.0,<8.0.0` to match the bundled Elasticsearch 7.17.13 container (frontend previously pinned to ES 5.x — mismatch fixed)
- All packages pinned to stable versions tested with **Python 3.11**
- `Flask-Caching==2.1.0` added to `requirements_frontend.txt`

### Docker
- All three Dockerfiles updated to `python:3.11-slim` (was `3.13.0a3-slim` alpha and `3.9-slim`)
- Fixed duplicate `pip install` in `scrapper.dockerfile`

### Harvesting / scripts
- `harvest.sh`: added `https://ahmia.fi/onions/` (full v3 onion list) as primary clearnet source; removed defunct tor2web service, dead deepdotweb/darkwebnews URLs, and all v2 onion directory sources
- `stronghold_paste_rip.sh`: removed dead v2 paste source (`nzxj65x32vh2fkhk.onion`); placeholder comment left for v3 replacement
- `extract_from_url.sh`, `tor_extract_from_url.sh`, `purify.sh`: fixed long-standing regex bug (`[0-9a-zA_Z]` → `[0-9a-zA-Z]`) that caused the A-Z range to not match correctly

### Bug fixes
- `tor_elasticsearch.py`: updated for Elasticsearch 7.x — `DocType` → `Document`, removed deprecated `doc_type`/`MetaField(parent)` from Meta, removed `elasticsearch.compat` (dropped in ES 7.x client), fixed `hits.total == 0` → `hits.total["value"] == 0`, removed deprecated `Index.doc_type()` calls, fixed `_parent` sort key → `_id`
- `tor_cache.py`: fixed `NameError` — `Response` was used in `is_redirect()` without being imported; now uses already-imported `flask.Response`
- `web/app.py`: fixed `NameError` in `bitcoins_list()` — `addr` was referenced but never defined in that scope; replaced with `None`
- `tor_db/__init__.py`: replaced `create_tables=True` (caused duplicate index errors with MariaDB InnoDB FK auto-indexing) with Python-based schema init (`lib/init_schema.py`) that reads `schema.sql`, skips `DROP TABLE` on restart, and ignores duplicate table/index errors — safe for both first run and container restarts
- `lib/init_schema.py`: new file — Python-based DB schema initializer using PyMySQL, runs at startup before PonyORM mapping
- `schema.sql`: fixed `idx_domain_title` key prefix from `title(65535)` → `title(191)` (MariaDB 10.5 InnoDB max key length is 3072 bytes; utf8 = 3 bytes/char → max 1024 chars)
- `lib/tor_db/models/domain.py`: changed `description_json = Optional(Json)` → `Optional(str, 10240)` — PonyORM's Json type generates `CAST(... AS JSON)` in MariaDB UPDATE WHERE clauses which is invalid syntax; storing as varchar string avoids this
- `torscraper/spiders/tor_scrapy.py`: fixed `parse()` returning bare `return` (None) in a generator decorated with `@db_session` — changed to `return []` to satisfy Scrapy's middleware iterable expectation; fixed `description_json` assignment to store JSON string via `json.dumps(json.loads(...))`
- `scrapper.dockerfile`: fixed `.cache` directory ownership — was created as root before `USER freshonions`, causing tldextract permission warning on every startup; now created with `chown freshonions:freshonions`
- `docker-compose.yml`: removed `version:` field (obsolete warning), removed `user: ${CURRENT_UID}` from all services (caused MariaDB and Tor proxy init failures), added MariaDB healthcheck with `condition: service_healthy` on all dependent services
- `scripts/bulk_insert_domains.py`: new script — bulk-inserts onion hostnames from a file directly into the DB via PyMySQL, bypassing the scraper (for pre-populating from Ahmia or other lists)

## Features

* Crawls the darknet looking for new hidden service
* Find hidden services from a number of clearnet sources
* Optional fulltext elasticsearch support
* Marks clone sites of the /r/darknet superlist
* Finds SSH fingerprints across hidden services
* Finds email addresses across hidden  services
* Finds bitcoin addresses across hidden services
* Shows incoming / outgoing links to onion domains
* Up-to-date alive / dead hidden service status
* Portscanner
* Search for "interesting" URL paths, useful 404 detection
* Automatic language detection
* Fuzzy clone detection (requires elasticsearch, more advanced than superlist clone detection)
* Docker containers to allow single node deployment
* Upgrade to Python3

## Licence

This software is made available under the GNU Affero GPL 3 License.. What this means is that is you deploy this software as part of networked software that is available to the public, you must make the source code available (and any modifications).

From the GNU site:

> The GNU Affero General Public License is a modified version of the ordinary GNU GPL version 3. It has one added requirement: if you run a modified program on a server and let other users communicate with it there, your server must also allow them to download the source code corresponding to the modified version running there

## Dependencies

* python
* tor 

### pip install:

pip install -r requirements.txt

## Install

Create mysql db from schema.sql

Edit etc/database for your database setup

Edit etc/proxy for your TOR setup

    script/push.sh someoniondirectory.onion 
    script/push.sh anotheroniondirectory.onion

Edit etc/uwsgi_only and set BASEDIR to wherever torscraper is installed (i.e. /home/user/torscraper)

Run:

    init/scraper_service.sh # to start crawling
    init/isup_service.sh # to keep site status up to date

### Optional ElasticSearch Fulltext Search

The torscraper comes with optional elasticsearch capability (enabled by default). Edit etc/elasticsearch and set vars or set ELASTICSEARCH_ENABLED=false to disable. Run scripts/elasticsearch_migrate.sh to perform the initial setup after configuration. 

if elasticsearch is disabled there will be no fulltext search, however crawling and discovering new sites will still work.

### cronjobs

    # harvest onions from various sources
    1 18 * * * /home/scraper/torscraper/scripts/harvest.sh
    
    # get ssh fingerprints for new sites
    1 4,16 * * * /home/scraper/torscraper/scripts/update_fingerprints.sh
    
    # mark sites as genuine / fake from the /r/darknetmarkets superlist    
    1 9 * * 1 /home/scraper/torscraper/scripts/get_valid.sh
    
    # scrape pastebin for onions (needs paid account / IP whitelisting)                 
    */5 * * * * /home/scraper/torscraper/scripts/pastebin.sh
    
    # portscan new onions               
    1 */6 * * * /home/scraper/torscraper/scripts/portscan_up.sh
    
    # scrape stronghold paste
    32 */2 * * * /home/scraper/torscraper/scripts/stronghold_paste_rip.sh
    
    # detect clones
    16 3 * * * /home/scraper/torscraper/scripts/detect_clones.sh


## Infrastructure

Fresh Onions runs on two servers, a frontend host running the database and hidden service web site, and a backend host running the crawler. Probably most interesting to the reader is the setup for the backend. TOR as a client is COMPLETELY SINGLETHREADED. I know! It's 2017, and along with a complete lack of flying cars, TOR runs in a single thread. What this means is that if you try to run a crawler on a single TOR instance you will quickly find you are maxing out your CPU at 100%.

The solution to this problem is running multiple TOR instances and connecting to them through some kind of frontend that will round-robin your requests. The Fresh Onions crawler runs eight Tor instances.

Debian (and ubuntu) comes with a useful program "tor-instance-create" for quickly creating multiple instances of TOR. I used Squid as my frontend proxy, but unfortunately it can't connect to SOCKS directly, so I used "privoxy" as an intermediate proxy. You will need one privoxy instance for every TOR instance. There is a script in "scripts/create_privoxy.sh" to help with creating privoxy instances on debian systems. It also helps to replace /etc/privoxy/default.filter with an empty file, to reduce CPU load by removing unnecessary regexes.

Additionally, this resource https://www.howtoforge.com/ultimate-security-proxy-with-tor might be useful in setting up squid. If all you are doing is crawling and don't care about anonymity, I also recommend running TOR in tor2web mode (required recompilation) for increased speed

## Docker compose

You can also run fresh onion locally, you'll need Docker and Docker compose.
'''
make all
'''

will build all the different containers: frontend, MySQL, scrapper, isup (alive check) and cron
connect to localhost:80 for web app, localhost:8080 for web database access
