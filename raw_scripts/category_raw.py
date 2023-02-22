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

catalog_table = glueContext.create_dynamic_frame.from_catalog(
    database="tickit",
    table_name="tickit_saas_category",
    transformation_ctx="catalog_table",
)

S3bucket_node3 = glueContext.getSink(
    path=f"s3://{args['s3_bucket']}/bronze/category/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=[],
    enableUpdateCatalog=True,
    transformation_ctx="S3bucket_node3",
)
S3bucket_node3.setCatalogInfo(
    catalogDatabase="tickit", catalogTableName="raw_tickit_category"
)
S3bucket_node3.setFormat("avro")
S3bucket_node3.writeFrame(catalog_table)
job.commit()