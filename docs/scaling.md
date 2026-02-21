# Scaling the Pipeline for Production

## Current State

The current pipeline is designed for a single-node environment — it watches one 
folder, processes files sequentially, and writes to a single PostgreSQL instance. 
This works well for moderate data volumes but would need significant changes to 
handle millions of files per day in a production environment.

---

## Bottlenecks at Scale

| Bottleneck | Problem |
|---|---|
| Single folder watcher | Can only monitor one directory on one machine |
| Sequential file processing | Files are processed one at a time |
| Single DB instance | One PostgreSQL node becomes a write bottleneck |
| No partitioning | Large tables slow down queries over time |
| In-memory file tracking | Processed files list is lost on restart |

---

## Proposed Scaled Architecture
```
+------------------+     +------------------+     +---------------------+
|                  |     |                  |     |                     |
|   IoT Devices /  | --> |   Apache Kafka   | --> |   Apache Spark      |
|   Data Sources   |     |   (Message Queue)|     |   (Stream Processing|
|                  |     |                  |     |    Cluster)         |
+------------------+     +--------+---------+     +----------+----------+
                                  |                          |
                         +--------v---------+      +---------v----------+
                         |                  |      |                    |
                         |   Kafka Topics   |      |  Validation &      |
                         |  (partitioned    |      |  Transformation    |
                         |   by device)     |      |  (distributed)     |
                         |                  |      |                    |
                         +------------------+      +---------+----------+
                                                             |
                                              +--------------+-----------+
                                              |                          |
                                   +----------v---------+   +-----------v--------+
                                   |                    |   |                    |
                                   |  PostgreSQL with   |   |   Data Warehouse   |
                                   |  Read Replicas     |   |   (Redshift /      |
                                   |                    |   |    BigQuery)       |
                                   +--------------------+   +--------------------+
```

---

## Key Technologies for Scaling

### 1. Apache Kafka — Message Queue
Instead of watching a folder, data sources publish messages to Kafka topics.

- Each IoT device or data source publishes to its own Kafka topic
- Kafka retains messages even if consumers are down — no data loss
- Multiple consumers can read from the same topic in parallel
- Handles millions of events per second with ease
- Built-in fault tolerance with message replication across brokers

**Why Kafka over a folder watcher?**
A folder watcher is a single point of failure and doesn't scale horizontally. 
Kafka decouples producers from consumers and allows the pipeline to scale 
each part independently.

---

### 2. Apache Spark — Distributed Processing
Replace the single-threaded pandas pipeline with Spark Structured Streaming.

- Processes data in parallel across a cluster of machines
- Can read directly from Kafka topics as a stream
- Handles validation, transformation, and aggregation at massive scale
- Fault tolerant — automatically recovers failed tasks on other nodes
- Can process both real-time streams and large historical batches

**Example Spark Streaming job:**
```python
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "sensor-data") \
    .load()
```

---

### 3. Cloud-Based Alternatives

If managing Kafka and Spark clusters is too complex, cloud services offer 
managed equivalents:

| Component | AWS | Google Cloud | Azure |
|---|---|---|---|
| Message Queue | AWS Kinesis | Cloud Pub/Sub | Event Hubs |
| Stream Processing | AWS Lambda | Dataflow | Stream Analytics |
| Data Warehouse | Redshift | BigQuery | Synapse Analytics |
| Object Storage | S3 | Cloud Storage | Blob Storage |

**Recommended cloud stack for this pipeline:**
- **AWS Kinesis** to replace the folder watcher and Kafka
- **AWS Lambda** for lightweight validation and transformation
- **AWS Glue** for heavy ETL and aggregation jobs
- **Amazon RDS (PostgreSQL)** with read replicas for storage
- **Amazon Redshift** for analytical queries on aggregated data

---

### 4. Database Scaling

The current single PostgreSQL instance would need these changes at scale:

- **Table partitioning** — partition `raw_sensor_data` by month so queries 
  don't scan the entire table
- **Read replicas** — offload analytical queries to replica nodes
- **Connection pooling** — use PgBouncer to manage thousands of concurrent 
  connections efficiently
- **Archiving** — move old data to cold storage (S3 / Glacier) automatically
- **Data warehouse** — move aggregated metrics to Redshift or BigQuery for 
  fast analytical queries across billions of rows

---

### 5. Containerization and Orchestration

For deploying and managing the pipeline at scale:

- **Docker** — containerize each pipeline component so it runs consistently 
  anywhere
- **Kubernetes** — orchestrate containers, auto-scale based on load, and 
  restart failed components automatically
- **Helm charts** — manage Kubernetes deployments for the pipeline

---

### 6. Monitoring and Observability

At scale, observability becomes critical:

- **Prometheus + Grafana** — monitor pipeline throughput, error rates, 
  and DB performance in real time
- **ELK Stack** (Elasticsearch, Logstash, Kibana) — centralized log 
  aggregation and searching across all pipeline nodes
- **PagerDuty / Alerting** — automated alerts when error rates spike or 
  pipeline lag increases

---

## Summary

| Component | Current | At Scale |
|---|---|---|
| Ingestion | Folder watcher | Apache Kafka / AWS Kinesis |
| Processing | Single-threaded pandas | Apache Spark / AWS Lambda |
| Storage | Single PostgreSQL | PostgreSQL + Redshift |
| Deployment | Local Python script | Docker + Kubernetes |
| Monitoring | Log files | Prometheus + Grafana + ELK |
| Fault Tolerance | Try/except + retries | Kafka retention + Spark recovery |

The current pipeline is built with clean separation of concerns — each component 
(watcher, validator, transformer, aggregator, db handler) is independent. This 
makes it straightforward to swap out individual components for their scaled 
equivalents without rewriting the entire pipeline.