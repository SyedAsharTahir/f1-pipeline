# F1 Data Pipeline

An ELT pipeline that loads Formula 1 World Championship data into Postgres, models it with dbt into a star schema, and orchestrates everything with Airflow. Historical data (1950 to 2024) comes from the Kaggle dataset, and 2025 onward is pulled from the Jolpica API.

## Status

| Stage | State |
|---|---|
| Postgres 16 in Docker Compose | Done |
| Raw loader (`loadRaw.py`), 14 tables | Done |
| Jolpica API loader for 2025 onward (`plugins/load_jolpica.py`) | Done |
| dbt staging layer, 14 models | Done |
| dbt marts: `dim_drivers`, `dim_constructors`, `dim_circuits`, `dim_status`, `dim_races` | Done |
| dbt mart: `fct_results` | Done |
| Airflow orchestration (Dockerized, dbt in its own venv) | Done |
| dbt tests (unique, not_null, relationships) | Planned |
| Dashboard and analysis | Planned |

## Architecture

```
Kaggle CSVs ----> loadRaw.py -----+
                                  +--> raw schema --> dbt staging (views) --> dbt marts (tables) --> dashboard
Jolpica API ----> load_jolpica.py +    (text copy)     clean, cast, rename       star schema          (planned)

                  Airflow (f1_pipeline DAG) schedules the loads and dbt runs
```

This is an ELT design. Data is loaded as-is, and all cleaning and modeling happens inside Postgres with dbt.

| Schema | Contents | Materialization |
|---|---|---|
| `raw` | Exact copy of each source table, every column stored as text | Tables |
| `staging` | One model per raw table: `\N` converted to NULL, types cast, columns renamed to snake_case | Views |
| `marts` | Star schema: dimension tables and a fact table | Tables |

### Why load everything as text

The source files use the literal string `\N` for missing values. Loading as text means the load never fails on bad values, keeps an untouched copy of the source, and puts all cleaning in one place (the staging layer), where it can be tested and rebuilt.

### Star schema

```
fct_results (one row per driver per race)
   |-- driver_id       -> dim_drivers
   |-- constructor_id  -> dim_constructors
   |-- race_id         -> dim_races (includes circuit name and country)
   |-- status_id       -> dim_status
```

`dim_circuits` is also available as a standalone dimension. `dim_races` carries `circuit_name`, `location` and `country`, so dashboards can filter races by circuit without an extra join.

## Tech stack

- Postgres 16 (Docker Compose)
- Apache Airflow 3.0 (Docker, custom image)
- dbt Core with the dbt-postgres adapter (installed in a separate venv inside the Airflow image)
- Python 3 with psycopg2 and python-dotenv (raw loading)

## Project structure

```
f1-pipeline/
|-- docker-compose.yml     # Postgres, Airflow metadata DB, Airflow
|-- Dockerfile             # Airflow image + dbt venv
|-- loadRaw.py             # loads Kaggle CSVs from data/ into the raw schema
|-- requirements.txt
|-- .env.example           # connection settings template
|-- data/                  # Kaggle CSVs (gitignored)
|-- dags/
|   `-- f1_pipeline.py     # f1_pipeline and weather_daily DAGs
|-- plugins/
|   `-- load_jolpica.py    # Jolpica API loader (2025 onward)
`-- f1_dbt/
    |-- dbt_project.yml
    |-- profiles.yml       # reads credentials from environment variables
    |-- macros/
    |   `-- generate_schema_name.sql   # use schema names as-is (staging, marts)
    `-- models/
        |-- staging/       # sources.yml + stg_* models
        `-- marts/         # dim_* and fct_* models
```

## Setup

### 1. Prerequisites

Docker with Compose, Python 3, and the Kaggle F1 CSV files.

### 2. Environment

```bash
cp .env.example .env
```

`.env` needs these variables:

```
POSTGRES_USER=f1
POSTGRES_PASSWORD=<your password>
POSTGRES_DB=f1
POSTGRES_PORT=5432
```

If another Postgres is already using port 5432, set `POSTGRES_PORT` to a different host port such as 5433. Inside the Docker network, containers always reach Postgres on 5432 via the `postgres` host.

### 3. Make dbt's output folders writable

`f1_dbt/` is bind-mounted into the Airflow container, which runs as a different user than you. Create the folders dbt writes to and open their permissions, or dbt fails with `Permission denied: .../dbt.log`:

```bash
mkdir -p f1_dbt/logs f1_dbt/target
chmod -R 777 f1_dbt/logs f1_dbt/target
```

### 4. Start the stack

```bash
docker compose up -d --build
```

Check that Airflow parsed the DAGs without errors:

```bash
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags list-import-errors
```

Verify dbt can connect from inside the container:

```bash
docker compose exec airflow bash -c "cd /opt/airflow/dbt && /opt/airflow/dbt_venv/bin/dbt debug"
```

### 5. Load the historical data

Download the Kaggle CSVs into `data/`, then from a local virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python loadRaw.py            # load every CSV in data/
python loadRaw.py circuits   # or load specific tables by name
```

Each table is dropped and recreated, so re-running is safe.

### 6. Run the pipeline

Unpause and trigger the DAG:

```bash
docker compose exec airflow airflow dags unpause f1_pipeline
docker compose exec airflow airflow dags trigger f1_pipeline
docker compose exec airflow airflow dags list-runs f1_pipeline
```

The Airflow UI is at http://localhost:8080. The `weather_daily` DAG is paused by default; unpause it the same way when you want it running.

### Running dbt manually (optional)

From your host, load `.env` into the shell first (repeat in each new terminal):

```bash
set -a; source .env; set +a
cd f1_dbt
dbt debug --profiles-dir .
dbt run --select staging --profiles-dir .
dbt run --select marts --profiles-dir .
```

## Verifying the load

After a successful run, the marts should line up with raw (counts below are from the run that includes 2025 data):

| Table | Rows |
|---|---|
| `raw.results` | 27,700 |
| `marts.fct_results` | 27,700 |
| `marts.dim_drivers` | 867 |
| `marts.dim_races` | 1,170 |

```bash
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -P pager=off \
  -c "SELECT (SELECT count(*) FROM raw.results) AS raw_results, (SELECT count(*) FROM marts.fct_results) AS fct_results;"
```

## Staging conventions

- `nullif("col", '\N')` on every column, so `\N` becomes a real NULL.
- Raw camelCase columns are quoted and renamed to snake_case (`raceId` becomes `race_id`).
- Whole numbers are cast to int, points to numeric, and date columns to date.
- Lap, qualifying and finishing times (for example `1:26.572`) are kept as text, because they are durations and not times of day.
- Generic names are prefixed to avoid clashes in joins (`race_name`, `circuit_name`, `finish_position`, and so on).

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Permission denied: /opt/airflow/dbt/logs/dbt.log` | Bind-mounted folder not writable by the container user. See setup step 3. |
| dbt connection refused inside the container | `host: localhost` points at the container itself. `profiles.yml` should read the host from `POSTGRES_HOST`, set to `postgres` in the Airflow service. |
| `\dt staging.*` shows nothing | Staging models are views. Query `information_schema.tables` or use `\dv`. |

## Roadmap

- Add dbt tests: unique and not_null on primary keys, relationships from `fct_results` to each dimension.
- Optional extra facts: `fct_lap_times`, `fct_pit_stops`, `fct_qualifying`.
- Dashboard and analysis on the marts schema.

## Data sources

- Formula 1 World Championship dataset from Kaggle, covering 1950 to 2024. The raw CSVs are not committed to this repository.
- [Jolpica F1 API](https://github.com/jolpica/jolpica-f1) for 2025 onward.
