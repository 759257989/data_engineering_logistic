"""
Phase 1 · 从 S3 stage 把 raw 数据灌进 Snowflake
-----------------------------------------------
对每个数据源:用 INFER_SCHEMA 自动建表 -> COPY INTO 灌数据 -> 数行数。

运行:  python src/ingestion/load_snowflake.py
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import snowflake.connector
from dotenv import load_dotenv

# 数据源映射:stage 里的子文件夹 -> 目标表名
# (先放核心三类;xlsx 的 7 张表想加的话,照同样格式补进来即可)
SOURCES = {
    "dataco": "DATACO_SUPPLY_CHAIN",
    "nyc_tlc": "NYC_TLC_TRIPS",
    "reference": "TAXI_ZONES",
}

STAGE = "S3_RAW_STAGE"
FILE_FORMAT = "PARQUET_FMT"


def build_create_sql(table: str, subpath: str) -> str:
    """生成"用 INFER_SCHEMA 自动建表"的 SQL。"""
    return (
        f"CREATE OR REPLACE TABLE {table} USING TEMPLATE ("
        f"SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) "
        f"FROM TABLE(INFER_SCHEMA("
        f"LOCATION => '@{STAGE}/{subpath}/', "
        f"FILE_FORMAT => '{FILE_FORMAT}')))"
    )


def build_copy_sql(table: str, subpath: str) -> str:
    """生成"按列名把数据从 stage 灌进表"的 COPY INTO SQL。"""
    return (
        f"COPY INTO {table} "
        f"FROM @{STAGE}/{subpath}/ "
        f"FILE_FORMAT = (TYPE = PARQUET) "
        f"MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE"
    )


def main() -> None:
    load_dotenv()
    # 建立连接;连接时就指定好 warehouse/database/schema,后面 SQL 就能用短名字
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )
    cur = conn.cursor()
    try:
        for subpath, table in SOURCES.items():
            print(f"\n[{table}] 建表中 ...")
            cur.execute(build_create_sql(table, subpath))   # 自动建表
            print(f"[{table}] 灌数据中 ...")
            cur.execute(build_copy_sql(table, subpath))      # COPY INTO
            n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # 数行数
            print(f"[{table}] 完成,共 {n:,} 行")
    finally:
        cur.close()
        conn.close()                                         # 用完关连接,warehouse 也会很快自动挂起


if __name__ == "__main__":
    main()