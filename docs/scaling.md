# Scaling the Pipeline

Right now the pipeline runs on a single machine and processes files one at a time 
which is fine for small volumes but won't work if we're dealing with millions of 
files a day. Here's how I'd think about scaling it horizontally.

## The Main Idea

Horizontal scaling means adding more machines to share the load instead of 
upgrading one big server. For this pipeline that means splitting the work across 
multiple nodes — one group of machines handles ingestion, another handles 
processing, another handles storage.

## Ingestion Layer

Instead of watching a single folder, I'd replace the file watcher with Apache Kafka. 
Data sources publish messages to Kafka topics and multiple consumer instances can 
read and process them in parallel across different machines. If one consumer goes 
down Kafka holds the messages until it recovers so nothing gets lost.

Google Cloud Pub/Sub is a managed alternative if we want to avoid running Kafka 
ourselves.

## Processing Layer

The pandas-based processing would be replaced with Apache Spark running in 
cluster mode. Spark splits the data across worker nodes and processes chunks 
in parallel. Validation, transformation and aggregation all happen distributedly 
instead of sequentially.

For lighter workloads AWS Lambda functions could handle individual file processing 
and scale automatically based on how many files are coming in.

## Storage Layer

The single PostgreSQL instance would need read replicas to handle more queries 
and table partitioning by date so the database doesn't slow down as data grows. 
For analytics specifically something like Amazon Redshift or BigQuery would be 
better suited than PostgreSQL.

## Optimizations

- Batch inserts instead of row by row (already doing this with execute_values)
- Compress CSV files before storing to reduce I/O
- Index the most queried columns (already done in schema)
- Cache aggregated results that are queried frequently