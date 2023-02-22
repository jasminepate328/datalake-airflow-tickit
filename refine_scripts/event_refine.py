import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

args = getResolvedOptions(sys.argv, ["JOB_NAME", "s3_bucket"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

event_table = glueContext.create_dynamic_frame.from_catalog(
    database="tickit",
    table_name="raw_tickit_event",
    transformation_ctx="event_table",
)

S3bucket_node3 = glueContext.getSink(
    path=f"s3://{args['s3_bucket']}/silver/event/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=[],
    compression="snappy",
    enableUpdateCatalog=True,
    transformation_ctx="S3bucket_node3",
)
S3bucket_node3.setCatalogInfo(
    catalogDatabase="tickit", catalogTableName="refined_tickit_event"
)
S3bucket_node3.setFormat("glueparquet")
S3bucket_node3.writeFrame(event_table)
job.commit()