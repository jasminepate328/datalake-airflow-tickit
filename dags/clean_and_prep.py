import os
from datetime import timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago

DAG_ID = os.path.basename(__file__).replace(".py", "")
S3_BUCKET = Variable.get("data_lake_bucket")

with DAG(
    dag_id=DAG_ID,
    description="Data Lake using BashOperator and AWS CLI",
    dagrun_timeout=timedelta(minutes=5),
    start_date=days_ago(1),
    schedule_interval=None,
    tags=["data lake"]
) as dag:
    begin = EmptyOperator(task_id="begin")
    end = EmptyOperator(task_id="end")

    delete_s3_objects = BashOperator(
        task_id="delete_s3_objects",
        bash_command=f'aws s3 rm "s3://{S3_BUCKET}/tickit/" --recursive'
    )

    delete_catalog = BashOperator(
        task_id="delete_catalog",
        bash_command='aws glue delete-database --name tickit'
    )

    list_s3_objects = BashOperator(
        task_id="list_s3_objects",
        bash_command=f"aws s3api list-objects-v2 --bucket {S3_BUCKET} --prefix tickit/"
    )

    create_catalog = BashOperator(
        task_id="create_catalog",
        bash_command="""aws glue create_database --database-input \ 
          '{"Name": "tickit", "Description": "Datasets from AWS E-commerce TICKIT relational database"}'
        """
    )

    chain(
        begin,
        (delete_s3_objects, delete_catalog, list_s3_objects, create_catalog),
        end
    )