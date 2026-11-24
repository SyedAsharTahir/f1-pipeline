# F1 Data Pipeline

An ELT pipeline that loads the Kaggle Formula 1 World Championship dataset (1950 to 2024) into Postgres and models it with dbt into a star schema for analytics and dashboarding.

## Status

| Stage | State |
|---|---|
| Postgres 16 in Docker Compose | Done |
| Raw loader (`loadRaw.py`), 14 tables | Done |
| dbt staging layer, 14 models | Done |
| dbt marts: `dim_drivers`, `dim_constructors`, `dim_circuits`, `dim_status`, `dim_races` | Done |
| dbt mart: `fct_results` | Done |
| dbt tests (`unique`, `not_null`, `relationships`) | Planned |
| Jolpica API loader for 2025 onward | Planned |
| Airflow scheduling | Planned |
| Power BI dashboard | Planned |

## Architecture

```
Kaggle CSVs -> loadRaw.py -> raw schema -> dbt staging (views) -> dbt marts (tables) -> Power BI
   (E)            (L)        (text copy)     clean, cast, rename     star schema          (planned)
```

This is an ELT design. The CSVs are loaded as-is, and all cleaning and modeling happens inside Postgres with dbt.

| Schema | Contents | Materialization |
|---|---|---|
| `raw` | Exact copy of each CSV, every column stored as `text` | Tables created by `loadRaw.py` |
| `staging` | One model per raw table: `\N` converted to NULL, types cast, columns renamed to snake_case | Views |
| `marts` | Star schema: dimension tables and a fact table | Tables |

### Why load everything as text

The source files use the literal string `\N` for missing values. Loading as text means the load never fails on bad values, keeps an untouched copy of the source, and puts all cleaning in one place (the staging layer), where it can be tested and rebuilt.

## Star schema

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
- Python 3 with `psycopg2` and `python-dotenv` (raw loading)
- dbt Core with the `dbt-postgres` adapter (staging and marts)
- Planned: Airflow (orchestration), Power BI (dashboard)

## Project structure

```
f1-pipeline/
|-- docker-compose.yml     # Postgres 16 service with healthcheck
|-- loadRaw.py             # loads CSVs from data/ into the raw schema
|-- requirements.txt
|-- .env.example           # connection settings template
|-- data/                  # Kaggle CSVs (gitignored)
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

Copy the template and fill in a password:

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

If another Postgres is already using port 5432, set `POSTGRES_PORT` to a different host port such as 5433.

### 3. Start Postgres

```bash
docker compose up -d --wait
```

`--wait` blocks until the healthcheck (`pg_isready`) passes.

### 4. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Load the raw data

Download the Kaggle CSVs into `data/`, then:

```bash
python loadRaw.py            # load every CSV in data/
python loadRaw.py circuits   # or load specific tables by name
```

Each table is dropped and recreated, so re-running is safe. Expected row counts include `circuits` 77, `races` 1,125, `drivers` 861, `results` 26,759 and `lap_times` 589,081.

### 6. Run dbt

dbt reads credentials from environment variables, so load `.env` into the shell first (repeat in each new terminal):

```bash
set -a; source .env; set +a
cd f1_dbt
dbt debug --profiles-dir .                  # connection check, expect "All checks passed!"
dbt run --select staging --profiles-dir .   # build the 14 staging views
dbt run --select marts --profiles-dir .     # build the marts
```

Run models by name with `--select` while any model file is still empty.

## Staging conventions

- `nullif("col", '\N')` on every column, so `\N` becomes a real NULL.
- Raw camelCase columns are quoted and renamed to snake_case (`raceId` becomes `race_id`).
- Whole numbers are cast to `int`, `points` to `numeric`, and date columns to `date`.
- Lap, qualifying and finishing times (for example `1:26.572`) are kept as text, because they are durations and not times of day.
- Generic names are prefixed to avoid clashes in joins (`race_name`, `circuit_name`, `finish_position`, and so on).

## Roadmap

1. Finish `fct_results` and verify the row count against `stg_results` (26,759).
2. Add dbt tests: `unique` and `not_null` on primary keys, `relationships` from `fct_results` to each dimension.
3. Optional extra facts: `fct_lap_times`, `fct_pit_stops`, `fct_qualifying`.
4. Jolpica API loader to extend the data from 2025 onward into the same raw layer.
5. Airflow DAG to schedule loading and dbt runs.
6. Power BI dashboard on the `marts` schema.

## Data source

Formula 1 World Championship dataset from Kaggle, covering 1950 to 2024. The raw CSVs are not committed to this repository.
