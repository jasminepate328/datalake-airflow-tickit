# datalake-airflow-tickit

Simple data pipeline using AWS's RDS, Glue, Athena, S3 and Apache AirFlow.

To test the environment:

- Create two RDS databases. I used the free tier version for MySQL and PostgreSQL, which has significant enough space to house data from the TICKIT data set (https://docs.aws.amazon.com/redshift/latest/gsg/cm-dev-t-load-sample-data.html). These two databases will be used as the source for the raw data.

Each database should have three tables 
venue(
	venueid smallint not null,
	venuename varchar(100),
	venuecity varchar(30),
	venuestate char(2),
	venueseats integer);
)
category(
	catid smallint not null,
	catgroup varchar(10),
	catname varchar(10),
	catdesc varchar(50));
)
event(
	eventid integer not null,
	venueid smallint not null,
	catid smallint not null,
	dateid smallint not null,
	eventname varchar(200),
	starttime timestamp);
)

- Create an Airflow environment and export dags into the s3 bucket of your choice. 
`aws s3 cp --recursive dags/ s3://<S3_BUCKET>/dags/`

- Create 2 Glue JDBC connecters, one for each database: `jdbc:<PROTOCOL>://<DATABASE_URL>:<PORT>/<DATABASE_NAME>`

- Create 2 Glue Data crawlers to extract schema infromation and metadata for the data sources. The crawlers will create 6 tables in the Glue Catalog to represent the 6 tables from the data sources.

![Cloud Architecture](https://user-images.githubusercontent.com/72892173/220223619-3c04c423-fc1b-4c47-bb11-f182b7367ed5.png)
