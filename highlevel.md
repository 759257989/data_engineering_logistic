# LogiFlow — 物流与车队运营数据平台 (High-Level Design)

> 一句话定位:把"订单业务数据 + 真实路线行程数据 + 自己生成的实时运营事件"整合成一个企业级数据平台,
> 用 **AWS S3 + Snowflake + dbt + Airflow + Confluent Kafka + Power BI** 跑通从数据采集、建模、编排、实时流到 BI 可视化的**完整数据工程闭环**。

---

## 1. 这个项目为什么有价值

普通项目说的是 "我分析了一份出租车数据";这个项目说的是 **"我从零搭了一个物流公司的数据平台"**。两者在简历和面试里完全不是一个量级。

它一次性覆盖了数据工程师岗位 JD 里几乎所有关键词:

- **数据采集 / Ingestion**:批量(batch)+ 实时(streaming)两条链路都有
- **数据湖 + 数据仓库**:AWS S3(raw zone)→ Snowflake(仓库)
- **维度建模 / Dimensional Modeling**:dbt 构建标准 star schema(事实表 + 维度表)
- **编排调度 / Orchestration**:Airflow DAG 管理依赖、重试、调度
- **实时流处理 / Streaming**:Kafka 接入自生成的事件流
- **数据质量 / 测试 / CI/CD**:dbt tests + GitHub Actions
- **BI / 可视化**:Power BI 面向 5 类不同角色的 dashboard
- **业务理解**:SLA 准时率、仓库吞吐、车队利用率、路线效率、运营风险

> **核心叙事(面试可直接用)**:我用 DataCo 供应链数据模拟订单与发货,用 NYC TLC 行程数据模拟真实路线执行,用自己生成的包裹扫描 / 仓库操作 / GPS / 车辆遥测事件模拟企业实时运营流;然后通过 S3、Snowflake、dbt、Airflow、Kafka 把它们整合成 star schema,最后用 Power BI 做了 5 个面向不同角色的运营 dashboard。

---

## 2. 整体架构

```
                        ┌──────────────── 批处理主干 (Batch) ─────────────────┐
                        │                                                      │
 源数据 (本地)          AWS S3              Snowflake                dbt        │   Power BI
 ┌────────────┐        ┌────────┐         ┌──────────┐         ┌────────────┐ │  ┌──────────┐
 │ DataCo CSV │──┐     │        │  COPY / │   RAW    │  dbt    │  STAGING   │ └─►│ 5 个     │
 │ NYC TLC    │──┼──►  │  raw   │─────────►  schema  │────────►│    +       │───►│ dashboard│
 │ xlsx       │──┘ 上传 │  zone  │ Snowpipe │ (原样)   │  run    │  MARTS     │   │ (按角色) │
 └────────────┘        └────────┘         └──────────┘         │(star schema)│  └──────────┘
                            ▲                   ▲               └────────────┘       ▲
                            │                   │                                    │
                            │     Airflow 统一编排所有批处理任务(调度/依赖/重试)      │
                            │                                                        │
 ┌──────────────────────┐  │   实时事件流 (Streaming)                                │
 │ 合成事件生成器        │  │  ┌─────────────────┐    ┌──────────────────┐           │
 │ · package scan       │──┴─►│ Confluent Cloud │───►│ consumer / connect│──────────┘
 │ · warehouse op       │     │   (Kafka)       │    │  → S3 / Snowflake │
 │ · driver GPS         │     └─────────────────┘    └──────────────────┘
 │ · vehicle telemetry  │
 └──────────────────────┘
```

**两条链路,一个仓库**:
- **批处理链路**(Phase 1–3):历史/业务数据 → S3 → Snowflake → dbt 建模,由 Airflow 编排。
- **实时链路**(Phase 4):自生成事件 → Kafka → 落进 Snowflake,和批处理数据在同一个仓库里汇合。

---

## 3. 数据源总览

| 数据源 | 体量(真实) | 在项目里的角色 | 回答什么问题 |
|---|---|---|---|
| **DataCo Smart Supply Chain** (CSV) | 180,519 行 × 53 列,latin-1 编码 | **业务层**:订单/客户/产品/发货/延迟/销售 | 谁下了什么订单?应该何时送达?是否延迟?哪些产品/地区/客户更易延迟?哪些发货影响利润? |
| **NYC TLC Trip Records** (parquet) | ≈955 万行 (2024 年 1–3 月,三个月合计) | **路线执行层**:把出租车行程抽象成"车队真实路线表现" | 路线实际跑了多久?实际距离多少?哪些区域慢?哪些路线成本高? |
| **Supply Chain Logistics Problem** (xlsx, 7 表) | OrderList 9,215 行 + 6 张约束表 | **补充层(可选)**:运费/仓储成本/运输通道 | 路线分配成本多少?哪条 lane 更贵?(用于成本/网络分析) |
| **taxi_zone_lookup** (CSV) | 265 个 zone | **维度**:把 NYC TLC 的 LocationID 翻译成 Borough/Zone 地名 | origin/destination 到底是哪个区? |
| **自生成事件流** (你来造) | 你控制(建议百万级) | **实时运营层**:包裹生命周期、仓库处理、GPS、车辆健康 | 包裹卡在哪个环节?哪个仓库 backlog 高?哪辆车有维护风险? |

> **关键设计点**:DataCo 回答"谁下单、是否延迟",NYC TLC 回答"车实际怎么跑",合成事件回答"过程中发生了什么"。三者在 Snowflake 里通过一张映射桥连起来(见 §5)。

---

## 4. 核心业务链路(数据如何串成一条线)

```
 客户 Customer
     │  下单
     ▼
 订单 Order ──────────────► 发货 Shipment ──────► 包裹 Package
                                                      │ 进入仓库
                                                      ▼
                                          仓库扫描/分拣 Warehouse Scan
                                                      │ 完成处理
                                                      ▼
                                          路线分配 Route Assignment ◄── (映射桥:连接 DataCo 与 NYC TLC)
                                                      │
                                       ┌──────────────┴──────────────┐
                                       ▼                              ▼
                                  司机 Driver                    车辆 Vehicle
                                       └──────────────┬──────────────┘
                                                      ▼
                                          路线执行 Trip / Route Execution  (NYC TLC 提供真实行程)
                                                      ▼
                                          配送结果 Delivered / Failed / Delayed
```

---

## 5. 目标数据模型 (Star Schema)

最终在 Snowflake 里用 dbt 构建成标准 **star schema**:中间是"事实表(facts,记录发生了什么、可累加的度量)",周围是"维度表(dimensions,描述事实的上下文)"。

### 事实表 (Facts)

| 事实表 | 粒度 (一行代表什么) | 来源 | 关键度量 |
|---|---|---|---|
| `fact_order_items` | 一个订单行项 | DataCo | sales, profit, quantity, discount |
| `fact_shipments` | 一次发货 | DataCo | 计划 vs 实际配送天数, delivery_status, late_delivery_risk |
| `fact_route_actuals` | 一趟行程 | NYC TLC | actual_distance, actual_duration, transport_cost |
| `fact_package_events` | 一条扫描事件 | 合成 | event_type, event_timestamp |
| `fact_warehouse_ops` | 一次仓库操作 | 合成 | processing_duration |
| `fact_vehicle_telemetry` | 一条遥测读数 | 合成 | fuel_level, engine_temp, maintenance_warning |

### 维度表 (Dimensions)

`dim_customer` · `dim_product` · `dim_category` · `dim_date` · `dim_zone`(NYC TLC zones)· `dim_warehouse` · `dim_vehicle` · `dim_driver` · `dim_shipping_mode`

### ⭐ 映射桥 `route_assignments`(本项目最巧妙的一环)

**问题**:DataCo 的 shipment 和 NYC TLC 的 trip 是两份毫不相干的数据,NYC TLC 里根本没有 `shipment_id`。

**解法**:造一张映射桥,把每个 shipment 合成地分配给一趟 trip + 一辆车 + 一个司机:

```
shipment_id  →  route_id  →  trip_id  →  vehicle_id  →  driver_id
   (DataCo)                  (NYC TLC)    (合成)        (合成)
```

分配逻辑用**固定随机种子**保证可复现,可选地按"日期窗口 + 距离合理性"匹配(让发货的承诺时效和行程时长大致对得上)。**这正是真实企业 dispatch / 路线分配系统的核心**,也是这个项目从"拼数据"升级成"建系统"的关键。这张桥在 Phase 2 用 dbt 构建。

---

## 6. 技术栈与企业角色对应

| 技术 | 在本项目的作用 | 对应的企业能力 |
|---|---|---|
| **AWS S3** | raw zone 数据湖,存放原样数据 | 云对象存储 / data lake |
| **Snowflake** | 云数据仓库,RAW + 建模后的表 | 云数仓 (类比 BigQuery/Redshift) |
| **dbt** | SQL 转换、star schema、数据测试、文档、血缘 | 现代数据栈核心 (Analytics Engineering) |
| **Apache Airflow** | 编排批处理:调度、依赖、重试、监控 | 工作流编排 |
| **Confluent Cloud (Kafka)** | 接入自生成的实时事件流 | 事件流 / 实时数据管道 |
| **Power BI** | 面向 5 类角色的 dashboard | 企业 BI |
| **GitHub Actions** | CI/CD:自动跑 dbt 测试、部署 | DevOps / DataOps |
| **DuckDB** (仅 Phase 0) | 本地零成本分析引擎,Snowflake 的本地预演 | 本地开发 / 数据剖析 |

---

## 7. 分阶段路线图

每个阶段都**能独立跑通、能单独拿出来展示**。强烈建议按顺序做:先把批处理主干(Phase 1–3)跑通,再叠加实时层(Phase 4)。

> 💡 **节奏建议**:Phase 0 全本地、零成本、不限时,可以慢慢打地基;**从 Phase 1 才开始开云账号**,然后尽量集中时间做完 Phase 1–5(因为 Snowflake 免费试用约 30 天、AWS/Confluent 有额度限制)。

### Phase 0 — 项目地基(全本地,零成本)
- **目标**:把三类数据彻底摸清,规范化后落到本地 raw 层,建立项目骨架。
- **交付物**:仓库目录结构 · Python 环境 · 数据剖析报告 · 本地 raw 层(parquet)· 数据字典 · README。
- **技术**:Python、DuckDB、pandas/pyarrow、git。
- **能展示**:你"懂数据"——知道每个字段含义、数据质量坑(编码、空值、异常值、PII)。
- 👉 **详见 `phase0.md`**

### Phase 1 — 云上 raw 层 (Ingestion)
- **目标**:把本地 raw 数据上传到 S3,再加载进 Snowflake 的 RAW schema。
- **交付物**:S3 bucket(raw zone)· Snowflake RAW 表 · 加载脚本(COPY INTO / Snowpipe)。
- **技术**:AWS S3、IAM(最小权限)、Snowflake、`snowflake-connector-python`。
- **能展示**:云数据采集、对象存储分区、仓库批量加载、密钥安全管理。

### Phase 2 — 维度建模 (Transformation)
- **目标**:用 dbt 把 RAW 转成 star schema,构建 §5 的事实/维度表和映射桥。
- **交付物**:dbt 项目(staging → marts)· star schema · dbt tests · 自动生成的文档与血缘。
- **技术**:dbt-core、Snowflake、Jinja/SQL。
- **能展示**:维度建模、数据测试、增量模型(incremental)、dev/prod 环境隔离。

### Phase 3 — 编排调度 (Orchestration)
- **目标**:用 Airflow DAG 把"S3 → Snowflake → dbt"整条批处理串起来,自动调度。
- **交付物**:Airflow DAG · 调度计划 · 重试/告警 · 任务依赖图。
- **技术**:Apache Airflow(本地 Docker 或 Astro CLI)。
- **能展示**:工作流编排、幂等设计、失败重试、可观测性。

### Phase 4 — 实时事件流 (Streaming)
- **目标**:写一个合成事件生成器,把包裹/仓库/GPS/遥测事件实时打进 Kafka,再消费落进仓库。
- **交付物**:事件生成器 · Kafka topics · consumer/connector · 仓库里的事件表 + 近实时聚合模型。
- **技术**:Confluent Cloud、`confluent-kafka` Python、(可选)Kafka Connect / Snowpipe Streaming。
- **能展示**:事件驱动架构、生产者/消费者、schema 设计、批流融合。

### Phase 5 — 分析与 BI (Visualization)
- **目标**:Power BI 连 Snowflake,做出 5 个面向不同角色的 dashboard。
- **交付物**:Executive / Delivery / Warehouse / Fleet / Route-Risk 五页报表。
- **技术**:Power BI(连接 Snowflake)、DAX。
- **能展示**:面向业务的 KPI 设计、数据故事化。
- ⚠️ **Mac 注意**:Power BI Desktop 仅 Windows。对策:Power BI Service(网页版)或 Windows 虚拟机(Parallels/UTM)。到 Phase 5 再决定。

### Phase 6 — 生产级加固 (Productionization)
- **目标**:把项目从"能跑"提升到"像生产系统"。
- **交付物**:GitHub Actions CI/CD · 数据质量门禁 · 新鲜度/告警监控 · 成本监控 · 完整文档。
- **技术**:GitHub Actions、dbt tests/freshness、(可选)Great Expectations。
- **能展示**:DataOps、自动化、可靠性、成本意识。

---

## 8. 五大分析方向 + 五个 Dashboard

| 分析方向 | 目标 | 核心指标 | Dashboard 页面 | 受众 |
|---|---|---|---|---|
| **Delivery SLA** | 配送是否准时 | On-Time Rate, Late Rate, Avg Delay, SLA Breach | Delivery Performance | Operations Manager |
| **Warehouse Throughput** | 仓库处理效率 | Packages/hr, Cycle Time, Backlog, Dock-to-Dispatch | Warehouse Operations | Warehouse Manager |
| **Fleet Utilization** | 车辆使用效率 | Utilization, Idle Time, Downtime, Fuel Eff., Maint. Warnings | Fleet Utilization | Fleet Manager |
| **Route Efficiency** | 路线是否高效 | Planned vs Actual, Cost/Mile, Delay Hotspots | Route & Risk | Dispatch / Planning |
| **Operational Risk** | 提前发现风险 | High-Risk Shipments, At-Risk Packages, Repeated-Delay Routes | (汇入 Route & Risk + Executive) | 管理层 |

外加一页 **Executive Overview**(给管理层):Total Shipments · On-Time Rate · SLA Breach · Warehouse Throughput · Fleet Utilization · High-Risk Shipments。

---

## 9. 贯穿全程的工程主题(initial 里缺失、本设计补上的部分)

这些是把项目从"作业"变成"企业级"的关键,会分散嵌入各阶段:

| 主题 | 做法 | 在哪个阶段 |
|---|---|---|
| **数据质量与测试** | dbt tests(unique/not_null/relationships)+ 源数据 freshness | Phase 2 / 6 |
| **维度建模规范** | 明确每个事实表的粒度(grain)、维度的 SCD 策略、命名规范 | Phase 2 |
| **增量加载与幂等** | dbt incremental models;DAG 可重跑不产生重复 | Phase 2 / 3 |
| **环境隔离** | Snowflake 用 database/schema 区分 dev 与 prod | Phase 2 |
| **密钥管理** | `.env` + `.gitignore`,绝不把 key 提交进 git;IAM 最小权限 | Phase 1 起 |
| **可观测性** | 数据新鲜度检查、DAG 失败告警、运行日志 | Phase 3 / 6 |
| **成本控制** | Snowflake warehouse 自动挂起(auto-suspend)、监控试用额度 | Phase 1 起 |
| **CI/CD** | GitHub Actions:PR 时自动跑 dbt 测试 | Phase 6 |
| **数据治理 / PII** | DataCo 含 Email/Password 等敏感字段,需在建模时屏蔽/脱敏 | Phase 2 |

---

## 10. 现实约束与对策

| 约束 | 影响 | 对策 |
|---|---|---|
| **Mac 上无法跑 Power BI Desktop** | Phase 5 | Power BI Service(网页)或 Windows 虚拟机;Phase 5 再定 |
| **Snowflake 免费试用 ≈ 30 天** | Phase 1–5 | 集中时间做云阶段;Phase 0 全本地不耗试用 |
| **AWS / Confluent 有免费额度** | Phase 1 / 4 | 控制数据量;用完即停;开启计费告警 |
| **DataCo 含 PII** | 全程 | raw 层保留、建模层脱敏;绝不外泄 |
| **新手学习曲线** | 全程 | 严格按阶段走,每阶段先跑通最小闭环再加复杂度 |

---

## 11. 目录结构(全程演进)

```
logistics_data/
├── highlevel.md              # 本文件:总体设计
├── phase0.md ... phase6.md   # 每个阶段的跟做指南
├── data/
│   ├── source/               # 原始下载文件(只读)
│   └── raw/                   # Phase 0 产出:规范化 raw 层
├── src/
│   ├── profiling/            # 数据剖析
│   ├── ingestion/            # 落 raw / 上传 S3 / 加载 Snowflake
│   └── streaming/            # Phase 4 事件生成器
├── dbt/                      # Phase 2 dbt 项目
├── airflow/                  # Phase 3 DAGs
├── dashboards/               # Phase 5 Power BI 文件与说明
├── docs/
│   └── data_dictionary.md    # 数据字典
├── .github/workflows/        # Phase 6 CI/CD
├── .env.example              # 密钥模板
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 12. 下一步

从 **`phase0.md`** 开始:全本地、零成本,把数据彻底摸清并落到 raw 层。打好这个地基,后面每一层都稳。
