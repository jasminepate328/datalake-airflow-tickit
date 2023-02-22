import sys

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.dynamicframe import DynamicFrameCollection
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext


# Script generated for node Custom transform
def MyTransform(glueContext, dfc) -> DynamicFrameCollection:
    from pyspark.sql.functions import when, col

    newdf = dfc.select(list(dfc.keys())[0]).toDF()
    newdf = newdf.withColumn(
        "month_int",
        when(col("month") == "JAN", 1)
            .when(col("month") == "FEB", 2)
            .when(col("month") == "MAR", 3)
            .when(col("month") == "APR", 4)
            .when(col("month") == "MAY", 5)
            .when(col("month") == "JUN", 6)
            .when(col("month") == "JUL", 7)
            .when(col("month") == "AUG", 8)
            .when(col("month") == "SEP", 9)
            .when(col("month") == "OCT", 10)
            .when(col("month") == "NOV", 11)
            .when(col("month") == "DEC", 12),
    )

    newdatedata = DynamicFrame.fromDF(newdf, glueContext, "newdatedata")
    return DynamicFrameCollection({"CustomTransform0": newdatedata}, glueContext)


args = getResolvedOptions(sys.argv, ["JOB_NAME", "s3_bucket"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node Data Catalog table
date_table = glueContext.create_dynamic_frame.from_catalog(
    database="tickit",
    table_name="raw_tickit_date",
    transformation_ctx="date_table",
)

# Script generated for node Custom transform
custom_transform = MyTransform(
    glueContext,
    DynamicFrameCollection(
        {"date_table": date_table}, glueContext
    ),
)

# Script generated for node Select From Collection
select_from_collection = SelectFromCollection.apply(
    dfc=custom_transform,
    key=list(custom_transform.keys())[0],
    transformation_ctx="select_from_collection",
)

# Script generated for node S3 bucket
S3bucket_node3 = glueContext.getSink(
    path=f"s3://{args['s3_bucket']}/silver/date/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=[],
    compression="snappy",
    enableUpdateCatalog=True,
    transformation_ctx="S3bucket_node3",
)
S3bucket_node3.setCatalogInfo(
    catalogDatabase="tickit", catalogTableName="refined_tickit_date"
)
S3bucket_node3.setFormat("glueparquet")
S3bucket_node3.writeFrame(select_from_collection)
job.commit()