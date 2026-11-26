FROM apache/airflow:3.0.2
RUN pip install --no-cache-dir apache-airflow-providers-postgres
RUN python -m venv /opt/airflow/dbt_venv \
 && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-postgres==1.9.0