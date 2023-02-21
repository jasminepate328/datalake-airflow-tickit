
import os
from datetime import timedelta

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.utils.dates import days_ago

DAG_ID = os.path.basename(__file__).replace(".py", '')
TABLES = ['users', 'venue', 'category', 'date', 'event', 'listing', 'sales']

with DAG(
    dag_id=DAG_ID,
    description='Run Glue Jobs',
    dagrun_timeout=timedelta(minutes=5),
    start_date=days_ago(1),
    schedule_interval=None,
    tags=['data lake', 'raw', 'bronze']
) as dag:
    begin = EmptyOperator(task_id='begin')
    end = EmptyOperator(task_id='end')

    list_glue_tables = BashOperator(
        task_id='list_glue_tables',
        bash_command="""aws glue get-tables --database-name tickit --query 'TableList[].Name' --expression "raw_*" --output table"""
    )

    for table in TABLES:
        start_jobs_raw = GlueJobOperator(
            task_id=f'start_job_{table}_raw', job_name=f'tickit_public_{table}_raw'
        )

        chain(
            begin,
            list_glue_tables,
            start_jobs_raw,
            end
        )