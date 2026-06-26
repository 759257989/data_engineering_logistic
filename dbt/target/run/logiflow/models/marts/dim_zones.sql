
  
    

create or replace transient table LOGIFLOW.DBT_DEV.dim_zones
    
    
    
    as (select
    md5(cast(coalesce(cast(location_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as zone_key,
    location_id,
    borough,
    zone,
    service_zone
from LOGIFLOW.DBT_DEV.stg_taxi__zones
    )
;


  