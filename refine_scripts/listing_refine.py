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

# Script generated for node Data Catalog table
listing_table = glueContext.create_dynamic_frame.from_catalog(
    database="tickit",
    table_name="raw_tickit_listing",
    transformation_ctx="listing_table",
)

# Script generated for node DropFields
drop_fields = DropFields.apply(
    frame=listing_table,
    paths=["totalprice"],
    transformation_ctx="drop_fields",
)

# Script generated for node S3 bucket
S3bucket_node3 = glueContext.getSink(
    path=f"s3://{args['s3_bucket']}/silver/listing/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=[],
    compression="snappy",
    enableUpdateCatalog=True,
    transformation_ctx="S3bucket_node3",
)
S3bucket_node3.setCatalogInfo(
    catalogDatabase="tickit", catalogTableName="refined_tickit_listing"
)
S3bucket_node3.setFormat("glueparquet")
S3bucket_node3.writeFrame(drop_fields)
job.commit()