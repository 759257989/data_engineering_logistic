"""
Phase 0 · 校验 raw 层 (Validate Raw Layer)
------------------------------------------
用 DuckDB 对比『源』和『raw』的行数是否一致,确保转换没丢行、没重复。

运行:  python src/ingestion/validate_raw.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import duckdb
from utils import SOURCE_DIR, RAW_DIR

con = duckdb.connect()


def rows(path_glob: str) -> int:
    """数 parquet(可含通配符)的总行数。"""
    return con.sql(f"SELECT count(*) FROM read_parquet('{path_glob}')").fetchone()[0]


# 1) 列出 raw 层每个文件的行数 / 列数
print("RAW 层清单:")
print("-" * 64)
for pq in sorted(RAW_DIR.rglob("*.parquet")):
    n = rows(str(pq))
    ncol = len(con.sql(f"DESCRIBE SELECT * FROM read_parquet('{pq}')").fetchall())
    print(f"{str(pq.relative_to(RAW_DIR)):<42}{n:>12,} 行 {ncol:>4} 列")

# 2) 关键校验:源行数 == raw 行数 ?
print("\n关键校验(源 行数 == raw 行数):")
print("-" * 64)

# DataCo:源是 latin-1 的 CSV,用 Python 数行数(减去表头那一行)
dataco_src = SOURCE_DIR / "dataco_supplychain_data" / "DataCoSupplyChainDataset.csv"
src_dataco = sum(1 for _ in open(dataco_src, encoding="latin-1")) - 1
raw_dataco = rows(str(RAW_DIR / "dataco" / "supply_chain.parquet"))
ok1 = src_dataco == raw_dataco
print(f"DataCo : 源 {src_dataco:>10,}  ==  raw {raw_dataco:>10,}   {'✓ 通过' if ok1 else '✗ 不一致!'}")

# NYC TLC:源和 raw 都是 parquet,直接数
src_nyc = rows(str(SOURCE_DIR / "yellow_tripdata_2024-*.parquet"))
raw_nyc = rows(str(RAW_DIR / "nyc_tlc" / "*.parquet"))
ok2 = src_nyc == raw_nyc
print(f"NYC TLC: 源 {src_nyc:>10,}  ==  raw {raw_nyc:>10,}   {'✓ 通过' if ok2 else '✗ 不一致!'}")

con.close()
print("\n 校验完成。" if (ok1 and ok2) else "\n  有不一致,请检查!")