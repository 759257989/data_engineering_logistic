"""
Phase 0 · 生成数据字典骨架 (Data Dictionary)
--------------------------------------------
数据字典 = 字段含义的"单一事实来源",团队任何人想查某列意思都来看它。
这里自动生成骨架:DataCo 部分用官方说明填好,其余你逐步补全。

运行:  python src/profiling/make_data_dictionary.py
输出:  docs/data_dictionary.md
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
from utils import SOURCE_DIR, RAW_DIR, PROJECT_ROOT, to_snake_case

con = duckdb.connect()
out = PROJECT_ROOT / "docs" / "data_dictionary.md"
out.parent.mkdir(parents=True, exist_ok=True)

lines = ["# 数据字典 (Data Dictionary)", "",
         ">---", ""]

# 读 DataCo 官方字段说明,做成 {snake_case 列名: 含义} 的映射
desc = pd.read_csv(
    SOURCE_DIR / "dataco_supplychain_data" / "DescriptionDataCoSupplyChain.csv",
    encoding="latin-1",
)
desc["field"] = desc["FIELDS"].map(to_snake_case)          # 列名转 snake_case 以便匹配
desc["text"] = desc["DESCRIPTION"].str.lstrip(": ").str.strip()  # 去掉开头的 ": "
meaning = dict(zip(desc["field"], desc["text"]))


def section(title: str, parquet_path: str, meanings=None) -> None:
    """为一个表生成一段 Markdown 表格:列名 / 类型 / 含义。"""
    lines.extend([f"## {title}", "", "| 列名 | 类型 | 含义 |", "|---|---|---|"])
    schema = con.sql(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").fetchdf()
    for _, r in schema.iterrows():
        col, typ = r["column_name"], r["column_type"]
        m = (meanings or {}).get(col, "")                 # DataCo 有官方说明,其余留空待填
        lines.append(f"| `{col}` | {typ} | {m} |")
    lines.append("")


section("DataCo Supply Chain", str(RAW_DIR / "dataco" / "supply_chain.parquet"), meaning)
section("NYC TLC Trip Records", str(RAW_DIR / "nyc_tlc" / "yellow_tripdata_2024-01.parquet"))
section("Taxi Zones", str(RAW_DIR / "reference" / "taxi_zones.parquet"))

out.write_text("\n".join(lines), encoding="utf-8")
con.close()
print(f"✓ 已生成 {out}")