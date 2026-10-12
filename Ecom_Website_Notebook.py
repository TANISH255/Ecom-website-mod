# Databricks notebook source
# MAGIC %pip install pymongo dnspython
# MAGIC from pyspark.sql.types import (
# MAGIC     StructType, StructField,
# MAGIC     StringType, LongType, IntegerType, TimestampType
# MAGIC )

# COMMAND ----------

# MAGIC %md
# MAGIC <div style="background-color: #ffebee; padding: 10px; border-left: 5px solid #c62828;">
# MAGIC   <strong>Storing Credentials:</strong> the 2 cells below are to store our db password and test if it is stored correctly.
# MAGIC </div>

# COMMAND ----------


# from getpass import getpass
# from databricks.sdk import WorkspaceClient

# w = WorkspaceClient()  # picks up your notebook's credentials automatically

# w.secrets.create_scope(scope="mongo-scope-final")
# w.secrets.put_secret(
#     scope="mongo-scope-final",
#     key="atlas-password",
#     string_value=getpass("Atlas password: "),
# )

# COMMAND ----------

# print([s.key for s in w.secrets.list_secrets(scope="mongo-atlas-scope")])

# COMMAND ----------

from getpass import getpass
from urllib.parse import quote_plus
from pymongo import MongoClient
from pyspark.sql.types import *
from delta.tables import DeltaTable
TABLE = "users_bronze"

user = "appuser"
pwd = dbutils.secrets.get(scope="mongo-scope-final", key="atlas-password")

uri = f"mongodb+srv://{quote_plus(user)}:{quote_plus(pwd)}@cluster0.zs4ydim.mongodb.net/mydb"
client = MongoClient(uri, serverSelectionTimeoutMS=8000)
print(client.mydb.users.count_documents({}))

# COMMAND ----------

schema = StructType([
    StructField("_id", StringType()),
    StructField("name", StringType()),
    StructField("phone", LongType()),
    StructField("address", StringType()),
    StructField("card", StringType()),
    StructField("card_month", IntegerType()),
    StructField("card_year", IntegerType()),
    StructField("card_cvv", IntegerType()), #As it is a dummy cvv so, for instance we can save them but, as per guidelines we can't save real cvv's.
    StructField("createdAt", TimestampType()),
    StructField("updatedAt", TimestampType()),
])

# COMMAND ----------

# Incremental filter: only fetch documents newer than what the table already has

query = {}
if spark.catalog.tableExists(TABLE):
    last = spark.sql(f"SELECT max(createdAt)AS m from {TABLE}").first()["m"]
    if last:
        query = {"createdAt":{"$gt" : last}}

# COMMAND ----------

#Helper to convert into int
def to_int(v):
    return int(v) if v is not None else None

# COMMAND ----------

#Turn Mongo documents into rows
rows = [
    (
        str(d["_id"]), d.get("name"), to_int(d.get("phone")), d.get("address"),
        d.get("card"), to_int(d.get("card_month")), to_int(d.get("card_year")),
        to_int(d.get("card_cvv")), d.get("createdAt"), d.get("updatedAt"),
    )
    for d in client.mydb.users.find(query)
]

# COMMAND ----------

#Test
#print(rows)

# COMMAND ----------

# Load only if there is something to load
if rows:
    df = spark.createDataFrame(rows, schema)

    # First run: create the table
    if not spark.catalog.tableExists(TABLE):
        df.write.format("delta").saveAsTable(TABLE)
        print(f"Created {TABLE} with {len(rows)} rows")

    # Later runs: merge (upsert)
    else:
        (DeltaTable.forName(spark, TABLE).alias("t")
            .merge(df.alias("s"), "t._id = s._id")
            .whenMatchedUpdateAll(condition="s.updatedAt > t.updatedAt")
            .whenNotMatchedInsertAll()
            .execute())

        # Report what the merge really did
        m = (DeltaTable.forName(spark, TABLE).history(1)
             .select("operationMetrics").first()[0])
        print(f"Fetched {len(rows)} | inserted {m.get('numTargetRowsInserted')} "
              f"| updated {m.get('numTargetRowsUpdated')}")
else:
    print("No new rows")

# Checking table location (runs after either branch)
spark.sql(f"DESCRIBE DETAIL {TABLE}").show(truncate=False)

# COMMAND ----------

#Final check 
spark.table("users_bronze").show(truncate=False)
display(spark.sql("DESCRIBE HISTORY users_bronze"))


# COMMAND ----------

