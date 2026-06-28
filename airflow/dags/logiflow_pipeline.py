"""
LogiFlow 批处理流水线 DAG
"""
from __future__ import annotations

from datetime import datetime, timedelta

# Airflow 3 的写法:DAG 从 airflow.sdk 导入;BashOperator 在 standard 这个 provider 里
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

# 你的项目根目录(改成你自己的绝对路径)
PROJECT_DIR = "/Users/yuwang/Desktop/logistics_data"
# 注意:这里用的是"项目 .venv"里的 python 和 dbt,不是 Airflow 那个 venv
VENV_PY = f"{PROJECT_DIR}/.venv/bin/python"
VENV_DBT = f"{PROJECT_DIR}/.venv/bin/dbt"


def alert_on_failure(context):
    """任意任务失败时触发。这里只打印告警;生产环境可改成发 Slack 或邮件。"""
    ti = context["task_instance"]
    print(f"[ALERT] 任务失败 dag={ti.dag_id} task={ti.task_id} run={context.get('run_id')}")


# 默认参数:套用到 DAG 里的每个任务
default_args = {
    "owner": "logiflow",
    "retries": 2,                          # 失败自动重试 2 次
    "retry_delay": timedelta(minutes=2),   # 每次重试间隔 2 分钟
    "on_failure_callback": alert_on_failure,
}

with DAG(
    dag_id="logiflow_batch_pipeline",
    description="raw -> S3 -> Snowflake -> dbt star schema",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),   # DAG 生效起点,填个过去的日期即可
    schedule="@daily",                  # 每天跑一次(Airflow 3 用 schedule,不是旧的 schedule_interval)
    catchup=False,                      # 关键:不要把起点到今天之间每一天都补跑一遍
    tags=["logiflow"],
) as dag:

    # 任务 1:上传本地 raw parquet 到 S3
    # 脚本本身用 python-dotenv 读 .env,所以 cd 到项目根目录就能拿到密钥
    upload_to_s3 = BashOperator(
        task_id="upload_to_s3",
        bash_command=f"cd {PROJECT_DIR} && {VENV_PY} src/ingestion/upload_to_s3.py",
    )

    # 任务 2:从 S3 把数据加载进 Snowflake 的 RAW 表
    load_snowflake = BashOperator(
        task_id="load_snowflake",
        bash_command=f"cd {PROJECT_DIR} && {VENV_PY} src/ingestion/load_snowflake.py",
    )

    # 任务 3:dbt build,建 staging + marts 并跑测试
    # dbt 不会自己读 .env,所以这里先 source .env 把 SNOWFLAKE_* 导入环境变量
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {PROJECT_DIR}/dbt && "
            f"set -a && source {PROJECT_DIR}/.env && set +a && "
            f"{VENV_DBT} build"
        ),
    )

    # 定义依赖顺序:用 >> 把三步串起来(上传 -> 加载 -> 建模)
    upload_to_s3 >> load_snowflake >> dbt_build