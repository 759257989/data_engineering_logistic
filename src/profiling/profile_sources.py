"""
Phase 0 · 数据剖析 (Data Profiling)
-----------------------------------
在动任何数据之前,先把每个数据源"看清楚":
多少行?每列什么类型?多少空值?有没有异常值/隐私字段?
你不可能对自己不了解的数据建模。

运行:  python src/profiling/profile_sources.py
"""
import sys
from pathlib import Path
# 让 Python 找得到我们写的 utils.py(把 src/ 加入搜索路径)
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import duckdb
from utils import SOURCE_DIR


def profile_df(df: pd.DataFrame, title: str) -> None:
    """打印一个 DataFrame 的体检报告:形状 + 每列(类型/空值率/唯一值数)。"""
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)
    print(f"行数: {len(df):,}    列数: {df.shape[1]}")
    print("-" * 78)
    print(f"{'列名':<32}{'类型':<14}{'空值%':>8}{'唯一值':>12}")
    print("-" * 78)
    for col in df.columns:
        null_pct = df[col].isna().mean() * 100      # 空值占比
        n_unique = df[col].nunique(dropna=True)     # 不同取值的数量
        print(f"{str(col):<32}{str(df[col].dtype):<14}{null_pct:>7.1f}%{n_unique:>12,}")


def profile_dataco() -> None:
    # ⚠️ DataCo 是 latin-1 编码,用默认 utf-8 读会直接报错——这是第一个数据质量坑
    path = SOURCE_DIR / "dataco_supplychain_data" / "DataCoSupplyChainDataset.csv"
    df = pd.read_csv(path, encoding="latin-1")
    profile_df(df, "DataCo Smart Supply Chain(业务主数据)")
    # 提醒:这份数据含 PII(个人隐私)字段,Phase 2 建模时要脱敏
    pii = [c for c in df.columns
           if any(k in c for k in ["Email", "Password", "Street", "Fname", "Lname"])]
    print(f"\n  发现 PII 敏感字段(后续需脱敏): {pii}")


def profile_xlsx() -> None:
    path = SOURCE_DIR / "Supply chain logistics problem.xlsx"
    sheets = pd.read_excel(path, sheet_name=None)   # sheet_name=None => 读全部 sheet,返回 {名字: DataFrame}
    for name, df in sheets.items():
        profile_df(df, f"xlsx · {name}")


def profile_zones() -> None:
    path = SOURCE_DIR / "taxi_zone_lookup.csv"
    df = pd.read_csv(path)
    profile_df(df, "taxi_zone_lookup(NYC 区域维度)")


def profile_nyc_tlc() -> None:
    """NYC TLC 约 955 万行,太大不适合全读进 pandas。
    改用 DuckDB:直接对 parquet 跑 SQL,不必把数据装进内存。
    DuckDB 在这里就是你本地的 Snowflake 预演——同样的 SQL,以后照搬上云。"""
    pattern = str(SOURCE_DIR / "yellow_tripdata_2024-*.parquet")  # * 通配 3 个月
    con = duckdb.connect()

    print("\n" + "=" * 78)
    print("  NYC TLC Trip Records(路线执行数据)— 用 DuckDB 剖析")
    print("=" * 78)

    # 1) 总行数
    n = con.sql(f"SELECT count(*) FROM read_parquet('{pattern}')").fetchone()[0]
    print(f"总行数: {n:,}")

    # 2) 日期范围(确认数据确实是 2024 年 1-3 月)
    dr = con.sql(f"""
        SELECT min(tpep_pickup_datetime) AS first_pickup,
               max(tpep_pickup_datetime) AS last_pickup
        FROM read_parquet('{pattern}')
    """).fetchdf()
    print("\n日期范围:")
    print(dr.to_string(index=False))

    # 3) 数据质量探针:统计明显异常的行(留到 staging 再清洗,这里只记录)
    dq = con.sql(f"""
        SELECT
            count(*) FILTER (WHERE trip_distance <= 0)                            AS zero_distance,
            count(*) FILTER (WHERE fare_amount   <  0)                            AS negative_fare,
            count(*) FILTER (WHERE tpep_dropoff_datetime <= tpep_pickup_datetime) AS bad_duration
        FROM read_parquet('{pattern}')
    """).fetchdf()
    print("\n数据质量探针(异常行先记录,留到 staging 阶段处理):")
    print(dq.to_string(index=False))

    con.close()


if __name__ == "__main__":
    profile_dataco()
    profile_xlsx()
    profile_zones()
    profile_nyc_tlc()
    print("\n 剖析完成。把发现的'坑'(编码/空值/PII/异常值)记进数据字典。")