
  create or replace   view LOGIFLOW.DBT_DEV.stg_taxi__zones
  
  
  
  
  as (
    with source as (
    select * from LOGIFLOW.RAW.taxi_zones
)
-- RAW 列名是小写、区分大小写,源列必须用双引号引用;输出别名保持不带引号。
select
    "location_id"::int as location_id,
    "borough"          as borough,
    "zone"             as zone,
    "service_zone"     as service_zone
from source
  );

