import os
from datetime import timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from airflow.utils.dates import days_ago

DAG_ID = os.path.basename(__file__).replace('.py', '')

S3_BUCKET = Variable.get('data_lake_bucket')
ATHENA_RESULTS = Variable.get("athena_query_results")

DEFAULT_ARGS = {
    "depends_on_past": False,
    "retries": 0,
    "email_on_failure": False,
    "email_on_retry": False,
    "output_location": f"s3://{ATHENA_RESULTS}/",
    "database": "tickit"
}

AGG_TICKIT_SALES_BY_CATEGORY = f"""
    CREATE TABLE IF NOT EXISTS agg_tickit_sales_by_category
    WITH (
        format = 'Parquet',
        write_compression = 'SNAPPY',
        external_location = 's3://{S3_BUCKET}/gold/tickit_sales_by_catergory/',
        partitioned_by = ARRAY ['catgroup', 'catname'],
        bucketed_by = ARRAY ['bucket_catname'],
        bucket_count = 1
    )
    AS WITH cat AS (
        SELECT DISTINCT e.eventid,
            c.catgroup,
            c.catname
        FROM refined_tickit_event AS e
            LEFT JOIN refined_tickit_category AS c ON c.catid = e.catid
    )
    SELECT cast(d.caldate AS DATE) AS caldate,
        s.pricepaid,
        s.qtysold,
        round(cast(s.pricepaid AS DECIMAL(8,2)) * s.qtysold, 2) AS sale_amount,
        cast(s.commission AS DECIMAL(8,2)) AS commission,
        round((cast(s.commission AS DECIMAL(8,2)) / (cast(s.pricepaid AS DECIMAL(8,2)) * s.qtysold)) * 100, 2) AS commission_prcnt,
        e.eventname,
        concat(u1.firstname, ' ', u1.lastname) AS seller,
        concat(u2.firstname, ' ', u2.lastname) AS buyer,
        c.catname AS bucket_catname,
        c.catgroup,
        c.catname
    FROM refined_tickit_sales AS s
        LEFT JOIN refined_tickit_listing AS l ON l.listid = s.listid
        LEFT JOIN refined_tickit_users AS u1 ON u1.userid = s.sellerid
        LEFT JOIN refined_tickit_users AS u2 ON u2.userid = s.buyerid
        LEFT JOIN refined_tickit_event AS e ON e.eventid = s.eventid
        LEFT JOIN refined_tickit_date AS d ON d.dateid = s.dateid
        LEFT JOIN cat AS c ON c.eventid = s.eventid;
"""

AGG_TICKIT_SALES_BY_DATE = f"""
    CREATE TABLE IF NOT EXISTS agg_tickit_sales_by_date
    WITH (
        format = 'Parquet',
        write_compression = 'SNAPPY',
        external_location = 's3://{S3_BUCKET}/tickit/gold/tickit_sales_by_date/',
        partitioned_by = ARRAY [ 'year', 'month'],
        bucketed_by = ARRAY [ 'bucket_month' ],
        bucket_count = 1
    )
    AS WITH cat AS (
        SELECT DISTINCT e.eventid,
            c.catgroup,
            c.catname
        FROM refined_tickit_event AS e
            LEFT JOIN refined_tickit_category AS c ON c.catid = e.catid
    )
    SELECT cast(d.caldate AS DATE) AS caldate,
        s.pricepaid,
        s.qtysold,
        round(cast(s.pricepaid AS DECIMAL(8,2)) * s.qtysold, 2) AS sale_amount,
        cast(s.commission AS DECIMAL(8,2)) AS commission,
        round((cast(s.commission AS DECIMAL(8,2)) / (cast(s.pricepaid AS DECIMAL(8,2)) * s.qtysold)) * 100, 2) AS commission_prcnt,
        e.eventname,
        concat(u1.firstname, ' ', u1.lastname) AS seller,
        concat(u2.firstname, ' ', u2.lastname) AS buyer,
        c.catgroup,
        c.catname,
        d.month AS bucket_month,
        d.year,
        d.month
    FROM refined_tickit_sales AS s
        LEFT JOIN refined_tickit_listing AS l ON l.listid = s.listid
        LEFT JOIN refined_tickit_users AS u1 ON u1.userid = s.sellerid
        LEFT JOIN refined_tickit_users AS u2 ON u2.userid = s.buyerid
        LEFT JOIN refined_tickit_event AS e ON e.eventid = s.eventid
        LEFT JOIN refined_tickit_date AS d ON d.dateid = s.dateid
        LEFT JOIN cat AS c ON c.eventid = s.eventid;
"""

QUERY_SALES_BY_DATE = """
    SELECT year(caldate) AS sales_year,
        month(caldate) AS sales_month,
        round(sum(sale_amount), 2) AS sum_sales,
        round(sum(commission), 2) AS sum_commission,
        count(*) AS order_volume
    FROM agg_tickit_sales_by_category
    GROUP BY year(caldate),
        month(caldate)
    ORDER BY year(caldate),
        month(caldate);"""

with DAG(
    dag_id=DAG_ID,
    description="Submit Amazon Athena CTAS queries",
    default_args=DEFAULT_ARGS,
    dagrun_timeout=timedelta(minutes=15),
    start_date=days_ago(1),
    schedule_interval=None,
    tags=["data lake", "aggregated", "gold"],
) as dag:
    begin = EmptyOperator(task_id="begin")

    begin_checks = EmptyOperator(task_id="begin_checks")

    end = EmptyOperator(task_id="end")

    athena_ctas_submit_category = AthenaOperator(
        task_id="athena_ctas_submit_category", query=AGG_TICKIT_SALES_BY_CATEGORY
    )

    athena_ctas_submit_date = AthenaOperator(
        task_id="athena_ctas_submit_date", query=AGG_TICKIT_SALES_BY_DATE
    )

    athena_query_by_date = AthenaOperator(
        task_id="athena_query_by_date", query=QUERY_SALES_BY_DATE
    )

    list_glue_tables = BashOperator(
        task_id="list_glue_tables",
        bash_command="""aws glue get-tables --database-name tickit \
                          --query 'TableList[].Name' --expression "agg_*"  \
                          --output table""",
    )

chain(
    begin,
    (athena_ctas_submit_category, athena_ctas_submit_date),
    begin_checks,
    (athena_query_by_date, list_glue_tables),
    end,
)