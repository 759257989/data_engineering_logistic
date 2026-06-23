"""
Phase 0 · 构建本地 raw 层 (Build Raw Layer)
-------------------------------------------
把 data/source/ 的原始文件,统一转成 data/raw/ 下的规范化 parquet。

raw 层的规矩(先理解再动手):
  ✓ 修正编码(latin-1 正确读出)           —— 让数据可读
  ✓ 列名规范化成 snake_case               —— 让后续 SQL 不用处处加引号
  ✓ 转成 parquet(列式 / 压缩 / 带类型)    —— 性能与标准
  ✗ 不改任何数据值、不删行、不补空值、不做业务逻辑
     这些"清洗"是下一层(staging)的事,raw 必须忠实于源。

运行:  python src/ingestion/build_raw_layer.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from utils import SOURCE_DIR, RAW_DIR, to_snake_case


def write_raw(df: pd.DataFrame, out_path: Path) -> None:
    """统一落盘:规范化列名 -> 写 parquet。"""
    df.columns = [to_snake_case(c) for c in df.columns]   # 列名转 snake_case
    out_path.parent.mkdir(parents=True, exist_ok=True)    # 目录不存在就自动建
    df.to_parquet(out_path, index=False)                  # 写 parquet(不保存行号)
    print(f"  ✓ {out_path.relative_to(RAW_DIR.parent)}  ({len(df):,} 行)")


def build_dataco() -> None:
    print("DataCo ->")
    src = SOURCE_DIR / "dataco_supplychain_data" / "DataCoSupplyChainDataset.csv"
    df = pd.read_csv(src, encoding="latin-1")             # 注意编码!
    write_raw(df, RAW_DIR / "dataco" / "supply_chain.parquet")


def build_xlsx() -> None:
    print("Supply Chain xlsx ->")
    src = SOURCE_DIR / "Supply chain logistics problem.xlsx"
    sheets = pd.read_excel(src, sheet_name=None)          # 读全部 7 张 sheet
    for name, df in sheets.items():
        fname = to_snake_case(name) + ".parquet"          # sheet 名也转 snake_case
        write_raw(df, RAW_DIR / "supply_chain_xlsx" / fname)


def build_zones() -> None:
    print("Taxi Zones ->")
    src = SOURCE_DIR / "taxi_zone_lookup.csv"
    df = pd.read_csv(src)
    write_raw(df, RAW_DIR / "reference" / "taxi_zones.parquet")


def build_nyc_tlc() -> None:
    print("NYC TLC ->")
    # 一个月一个文件地处理(每个约 50MB,单读没问题),保留按月分文件
    for src in sorted(SOURCE_DIR.glob("yellow_tripdata_2024-*.parquet")):
        df = pd.read_parquet(src)
        write_raw(df, RAW_DIR / "nyc_tlc" / src.name)


if __name__ == "__main__":
    print("开始构建本地 raw 层...\n")
    build_dataco()
    build_xlsx()
    build_zones()
    build_nyc_tlc()
    print(f"\n raw 层已生成于: {RAW_DIR}")