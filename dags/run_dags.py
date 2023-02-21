import os
from datetime import timedelta

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago

DAG_ID = os.path.basename(__file__).replace('.py', '')

with DAG(
    dag_id=DAG_ID,
    description="Run all DAGs",
    dagrun_timeout=timedelta(minutes=30),
    start_date=days_ago(1),
    schedule_interval=None,
    tags=["data lake"]
) as dag:
    begin = EmptyOperator(task_id="begin")

    end = EmptyOperator(task_id="end")

    trigger_dag_01 = TriggerDagRunOperator(
        task_id="trigger_dag_01",
        trigger_dag_id="data_lake__clean_and_prep",
        wait_for_completion=True,
    )

    trigger_dag_02 = TriggerDagRunOperator(
        task_id="trigger_dag_02",
        trigger_dag_id="data_lake__run_glue_crawler_source",
        wait_for_completion=True,
    )

    trigger_dag_03 = TriggerDagRunOperator(
        task_id="trigger_dag_03",
        trigger_dag_id="data_lake__run_glue_jobs_raw",
        wait_for_completion=True,
    )

    trigger_dag_04 = TriggerDagRunOperator(
        task_id="trigger_dag_04",
        trigger_dag_id="data_lake__run_glue_jobs_refined",
        wait_for_completion=True,
    )
    trigger_dag_05 = TriggerDagRunOperator(
        task_id="trigger_dag_05",
        trigger_dag_id="data_lake__submit_athena_queries",
        wait_for_completion=True,
    )

chain(
    begin,
    trigger_dag_01,
    trigger_dag_02,
    trigger_dag_03,
    trigger_dag_04,
    trigger_dag_05,
    end,
)