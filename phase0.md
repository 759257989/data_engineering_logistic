# Phase 0 — 项目地基(全本地 · 零成本)

> 本阶段一句话:**先把数据彻底摸清,再统一落成规范的本地 raw 层**。不碰云、不花钱,可以慢慢做。
> 打好这个地基,后面 Snowflake / S3 / dbt 每一层都稳。

---

## 🎯 Phase 0 目标

做完这一章,你会拥有:

1. 一个**结构清晰的项目仓库**(目录分好、git 管起来)。
2. 一个隔离的 **Python 虚拟环境**(依赖不污染系统)。
3. 一份**数据剖析报告**:每个数据源有多少行、每列什么类型、空值率、有哪些数据质量坑。
4. 一个**本地 raw 层**:三类数据统一转成规范化的 parquet。
5. 一份**数据字典**:每个字段是什么意思,有据可查。

> 💡 **为什么从这里开始?** 真实工作里,数据工程师 80% 的事故都源于"没搞懂数据就开始建模"。Phase 0 就是逼你先"看清楚再动手"。这也是面试里最能体现你"懂数据"的部分。

---

## 🗺️ Phase 0 在整条链路的位置

```
  [data/source]        [data/raw]              (Phase 1+)
  原始下载文件   ──►   规范化 parquet   ──►   S3 → Snowflake → dbt → Power BI
     │                    ▲
     │   Phase 0 就做这一段:摸清 + 规范化
     └────────────────────┘
```

Phase 0 = 把杂乱的原始文件(不同格式、不同编码、奇怪的列名)整理成**干净、统一、可信**的本地 raw 层。这正是后面所有云上工作的输入。

---

## 🧠 动手前,先理解 3 个核心概念

**① 分层架构(raw → staging → marts)**
企业数据平台不会把原始数据直接拿来用,而是分层处理:
- **raw**:原始数据的忠实副本,只换格式、不改内容。出任何问题都能回到这里重来。
- **staging**:清洗(改类型、补空值、统一单位、脱敏)。← Phase 2 做
- **marts**:面向分析的 star schema(事实表 + 维度表)。← Phase 2 做

Phase 0 只做 **raw**。记住 raw 的铁律:**只规范格式,绝不改数据值。**

**② 为什么用 Parquet 而不是 CSV?**
| | CSV | Parquet |
|---|---|---|
| 存储 | 纯文本,体积大 | 列式压缩,体积小很多 |
| 类型 | 没有(全是字符串) | 自带类型(日期就是日期) |
| 读取 | 整行扫描,慢 | 只读需要的列,快 |
Parquet 是云数仓(Snowflake/BigQuery)和数据湖的事实标准。raw 层统一用它。

**③ 为什么必须先做 Profiling(数据剖析)?**
你不可能对自己不了解的数据建模。剖析就是给数据做"体检":多少行、什么类型、多少空值、有没有异常值、有没有隐私字段。**先体检,再治疗。**

---

## ✅ 前置条件

确认有 Python 3(你的机器已装 Anaconda,满足):

```bash
python3 --version      # 应显示 3.9 或更高
```

> 📁 后面所有命令都在项目根目录 `/Users/yuwang/Desktop/logistics_data` 下执行。

---

## Step 1 · 建目录结构 + 归置源文件

当前你的原始文件散落在根目录。先建好结构,把它们收进 `data/source/`(只读,以后不再动它)。

```bash
# 1) 创建目录骨架
mkdir -p data/source data/raw
mkdir -p src/profiling src/ingestion
mkdir -p docs

# 2) 把原始文件移进 data/source/(xlsx 名字有空格,要加引号)
mv dataco_supplychain_data \
   "Supply chain logistics problem.xlsx" \
   yellow_tripdata_2024-*.parquet \
   taxi_zone_lookup.csv \
   data/source/
```

完成后结构应是:

```
logistics_data/
├── data/
│   ├── source/                      ← 原始文件(只读)
│   │   ├── dataco_supplychain_data/
│   │   ├── Supply chain logistics problem.xlsx
│   │   ├── yellow_tripdata_2024-01.parquet
│   │   ├── yellow_tripdata_2024-02.parquet
│   │   ├── yellow_tripdata_2024-03.parquet
│   │   └── taxi_zone_lookup.csv
│   └── raw/                         ← Phase 0 会往这里写
├── src/
│   ├── profiling/
│   └── ingestion/
└── docs/
```

> ⚠️ `data/source/dataco_supplychain_data/` 里有个 `tokenized_access_logs.csv`(95MB),那是网站访问日志,**和物流无关,本项目不用**,忽略即可。

---

## Step 2 · Python 虚拟环境 + 依赖

**虚拟环境**就是给本项目单独开一个"干净的 Python 房间",装的包只属于这个项目,不会和系统或别的项目打架。这是专业做法。

```bash
# 1) 创建虚拟环境(会生成一个 .venv 文件夹)
python3 -m venv .venv

# 2) 激活它(激活后命令行前面会出现 (.venv) 字样)
source .venv/bin/activate

# 3) 升级 pip
pip install --upgrade pip
```

新建 `requirements.txt`,写入本阶段需要的库:

```text
pandas        # 表格数据处理
pyarrow       # 读写 parquet
duckdb        # 本地 SQL 引擎(Snowflake 的本地预演)
openpyxl      # 读 .xlsx
```

安装:

```bash
pip install -r requirements.txt
```

> 💡 以后每次开新终端做这个项目,先 `source .venv/bin/activate` 激活环境。

---

## Step 3 · 写共享工具 `src/utils.py`

先写一个所有脚本都会用到的小工具:统一的路径定义 + 列名规范化函数。

新建 **`src/utils.py`**:

```python
"""共享工具:统一的路径定义 + 列名规范化函数。"""
from pathlib import Path
import re

# 项目根目录 = 本文件(src/utils.py)往上两级
# parents[0] 是 src/,parents[1] 是项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "data" / "source"   # 原始文件
RAW_DIR = PROJECT_ROOT / "data" / "raw"          # raw 层输出


def to_snake_case(name: str) -> str:
    """把任意列名转成 snake_case(全小写 + 下划线分隔)。

    例:'Days for shipping (real)' -> 'days_for_shipping_real'
        'PULocationID'            -> 'pu_location_id'

    这是一种机械、无损的规范化:只改名字格式,不改数据本身,
    所以放在 raw 层是允许的。目的是让后续 SQL 不必给列名处处加引号。
    """
    name = str(name).strip()
    name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name)    # 驼峰边界:aB -> a_B
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '_', name)  # 缩写边界:ABCd -> AB_Cd
    name = re.sub(r'[^0-9a-zA-Z]+', '_', name)             # 空格/括号/符号 -> _
    name = re.sub(r'_+', '_', name)                        # 多个 _ 合并成一个
    return name.strip('_').lower()                         # 去掉首尾 _ 并转小写
```

---

## Step 4 · 数据剖析 `src/profiling/profile_sources.py`

这一步给每个数据源做"体检"。注意我们对**小数据用 pandas**(直观),对**大数据(NYC TLC ≈955 万行)用 DuckDB**(直接对文件跑 SQL,不必塞进内存)——这正是"按数据规模选工具"的真实工程判断。

新建 **`src/profiling/profile_sources.py`**:

```python
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
    print(f"\n⚠️  发现 PII 敏感字段(后续需脱敏): {pii}")


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
    print("\n✅ 剖析完成。把发现的'坑'(编码/空值/PII/异常值)记进数据字典。")
```

运行:

```bash
python src/profiling/profile_sources.py
```

**怎么读这份报告?** 重点看四件事:
- **空值%**:某列空值很高(比如 DataCo 的 `Order Zipcode`),说明它不可靠,建模时要小心。
- **唯一值**:能帮你判断哪列是"主键候选"(唯一值数 ≈ 行数)。
- **PII 提醒**:记住哪些列是隐私字段,Phase 2 要脱敏。
- **数据质量探针**:NYC TLC 里那些零距离、负车费、时长为负的行——这些是真实世界数据的常态,先记下来。

---

## Step 5 · 构建本地 raw 层 `src/ingestion/build_raw_layer.py`

把 `data/source/` 的原始文件,统一转成 `data/raw/` 下的规范化 parquet。

新建 **`src/ingestion/build_raw_layer.py`**:

```python
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
    print(f"\n✅ raw 层已生成于: {RAW_DIR}")
```

运行:

```bash
python src/ingestion/build_raw_layer.py
```

完成后 `data/raw/` 会长这样:

```
data/raw/
├── dataco/supply_chain.parquet
├── nyc_tlc/yellow_tripdata_2024-01.parquet   (+ 02, 03)
├── supply_chain_xlsx/order_list.parquet       (+ 其余 6 张)
└── reference/taxi_zones.parquet
```

---

## Step 6 · 校验 raw 层 `src/ingestion/validate_raw.py`

raw 层必须**忠实于源**。每次搬运数据后都要验证"数量对得上"——这是最基本也最重要的工程习惯。

新建 **`src/ingestion/validate_raw.py`**:

```python
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
print("\n✅ 校验完成。" if (ok1 and ok2) else "\n❌ 有不一致,请检查!")
```

运行:

```bash
python src/ingestion/validate_raw.py
```

预期:DataCo 显示 **180,519** 行、NYC TLC 共 **9,554,778**(≈955 万)行,两项都 `✓ 通过`。

---

## Step 7 · 生成数据字典 `src/profiling/make_data_dictionary.py`

**数据字典**是"每个字段什么意思"的单一事实来源。DataCo 自带官方字段说明,我们直接拿来填;其余的边做边补。

新建 **`src/profiling/make_data_dictionary.py`**:

```python
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
         "> Phase 0 自动生成的骨架,请逐步补全『含义』列。", ""]

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
```

运行:

```bash
python src/profiling/make_data_dictionary.py
```

打开 `docs/data_dictionary.md`,你会看到 DataCo 的字段含义已自动填好;NYC TLC / Zones 的含义列留空,**自己补上**(这一步逼你真正理解每个字段)。

---

## Step 8 · 配置文件 + 用 git 管起来

新建 **`.gitignore`**(告诉 git 哪些不要提交——大数据文件和密钥绝不进仓库):

```text
# 数据文件不进 git(太大,且可能含 PII)
data/

# 密钥
.env

# Python
__pycache__/
*.pyc
.venv/

# 系统 / 编辑器
.DS_Store
.ipynb_checkpoints/
```

新建 **`.env.example`**(密钥模板,Phase 1 才填真实值;真实的 `.env` 永不提交):

```text
# AWS (Phase 1)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# Snowflake (Phase 1)
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_ROLE=
```

新建 **`README.md`**(项目门面):

```markdown
# LogiFlow — 物流与车队运营数据平台

把订单业务数据(DataCo)、真实路线数据(NYC TLC)、自生成的实时运营事件,
整合成企业级数据平台:S3 → Snowflake → dbt → Airflow → Kafka → Power BI。

- 总体设计见 `highlevel.md`
- 分阶段指南见 `phase0.md` ... `phase6.md`

## 快速开始(Phase 0)
\`\`\`bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/profiling/profile_sources.py
python src/ingestion/build_raw_layer.py
python src/ingestion/validate_raw.py
python src/profiling/make_data_dictionary.py
\`\`\`
```

初始化 git 并提交第一版:

```bash
git init
git add .
git commit -m "Phase 0: 项目地基 + 本地 raw 层"
```

> 💡 提交前,git 会自动忽略 `data/` 和 `.env`(因为 `.gitignore`)。可以 `git status` 确认大文件和密钥确实没被纳入。

---

## ✅ Phase 0 验收清单

逐项打勾,全过 = Phase 0 完成:

- [ ] 目录结构建好,源文件已在 `data/source/`
- [ ] 虚拟环境能激活,`pip install` 无报错
- [ ] `profile_sources.py` 跑通,看懂了空值/唯一值/PII/异常值报告
- [ ] `build_raw_layer.py` 跑通,`data/raw/` 下生成了所有 parquet
- [ ] `validate_raw.py` 两项校验都 `✓ 通过`(DataCo = 180,519 行)
- [ ] `docs/data_dictionary.md` 已生成,且补全了 NYC TLC / Zones 的含义
- [ ] `git commit` 成功,且 `data/`、`.env` 未被提交

---

## 🎓 你在 Phase 0 学到了什么

- **分层架构**:raw 只规范格式、不改数据;清洗留给 staging。
- **按规模选工具**:小数据 pandas,大数据 DuckDB(本地 SQL,Snowflake 预演)。
- **数据质量意识**:编码坑、空值、异常值、PII,都要先发现并记录。
- **可复现与可信**:虚拟环境 + 行数校验 + 数据字典 + git 版本管理。

这些正是数据工程师的基本功,面试里能直接讲。

---

## ➡️ 下一步:Phase 1

Phase 0 的产物(`data/raw/` 的规范化 parquet)就是 Phase 1 的输入。
**Phase 1 开始上云**:注册 AWS 与 Snowflake → 把 raw parquet 上传到 S3 → 加载进 Snowflake 的 RAW schema。

> 提醒:Snowflake 免费试用约 30 天。**等你准备好集中做 Phase 1–5 时,再去注册云账号**,避免试用期空转。
