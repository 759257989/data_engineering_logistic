
  create or replace   view LOGIFLOW.DBT_DEV.stg_nyc__trips
  
  
  
  
  as (
    with source as (
    select * from LOGIFLOW.RAW.nyc_tlc_trips
),
renamed as (
    -- RAW 列名是小写、区分大小写,源列必须用双引号引用。
    -- tpep_pickup/dropoff_datetime 在 RAW 里是"微秒级 epoch"整数(如 1709252331000000),
    -- 不能直接 ::timestamp_ntz(会当成秒,年份溢出);用 to_timestamp_ntz(x, 6) 按微秒解析。
    select
        "vendor_id"::int                              as vendor_id,
        to_timestamp_ntz("tpep_pickup_datetime", 6)   as pickup_ts,
        to_timestamp_ntz("tpep_dropoff_datetime", 6)  as dropoff_ts,
        "pu_location_id"::int                         as pickup_location_id,
        "do_location_id"::int                         as dropoff_location_id,
        "trip_distance"::float                        as trip_distance_miles,
        "fare_amount"::float                          as fare_amount,
        "tolls_amount"::float                         as tolls_amount,
        "congestion_surcharge"::float                 as congestion_surcharge,
        "total_amount"::float                         as total_amount,
        "passenger_count"::int                        as passenger_count
    from source
),
cleaned as (
    select
        -- NYC 数据没有行程 ID,用几个(已清洗的)字段哈希出一个稳定的代理 trip_id
        md5(cast(coalesce(cast(pickup_ts as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(dropoff_ts as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(pickup_location_id as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(dropoff_location_id as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(trip_distance_miles as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(fare_amount as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as trip_id,
        vendor_id,
        pickup_ts,
        dropoff_ts,
        pickup_location_id,
        dropoff_location_id,
        trip_distance_miles,
        -- 用上下车时间算出行程时长(分钟)
        datediff(minute, pickup_ts, dropoff_ts) as trip_duration_minutes,
        fare_amount,
        tolls_amount,
        congestion_surcharge,
        total_amount,
        passenger_count
    from renamed
    -- 这里就是 Phase 0 发现的脏数据"治疗现场":把零距离、负车费、
    -- 上车晚于下车、以及不在 2024 年 1-3 月的异常行,全部过滤掉
    where trip_distance_miles > 0
      and fare_amount >= 0
      and dropoff_ts > pickup_ts
      and pickup_ts >= '2024-01-01'::timestamp_ntz
      and pickup_ts <  '2024-04-01'::timestamp_ntz
)
select * from cleaned
  );

