from datetime import datetime,timedelta
from airflow.sdk import DAG,task # type: ignore
from airflow.providers.standard.operators.bash import BashOperator # type: ignore

DBT="/opt/airflow/dbt_venv/bin/dbt"
DBT_DIR="/opt/airflow/dbt"

with DAG(
    dag_id="f1_pipeline",
    schedule="0 6 * * 1",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["f1"],
)as dag:
    @task(execution_timeout=timedelta(minutes=30))
    def load_new_races():
        import load_jolpica
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        conn=PostgresHook(postgres_conn_id="f1_postgres").get_conn()
        load_jolpica.main(conn)

    dbt_run=BashOperator(task_id="dbt_run",bash_command=f"cd {DBT_DIR }&& {DBT} run",retries=0,)
    dbt_test=BashOperator(task_id="dbt_test",bash_command=f"cd {DBT_DIR }&& {DBT} test",retries=0,)
    load_new_races()>>dbt_run>>dbt_test



