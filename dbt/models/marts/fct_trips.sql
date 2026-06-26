with trips as (
    select * from {{ ref('stg_nyc__trips') }}
)
select
    trip_id,
    {{ dbt_utils.generate_surrogate_key(['pickup_location_id']) }}  as pickup_zone_key,   -- 外键 -> dim_zones
    {{ dbt_utils.generate_surrogate_key(['dropoff_location_id']) }} as dropoff_zone_key,
    {{ dbt_utils.generate_surrogate_key(['cast(pickup_ts as date)']) }} as pickup_date_key,
    pickup_ts,
    dropoff_ts,
    pickup_location_id,
    dropoff_location_id,
    trip_distance_miles,
    trip_duration_minutes,
    fare_amount,
    total_amount,
    -- 每英里成本:用车费除以距离(距离为 0 的已在 staging 过滤,这里再防一手)
    case when trip_distance_miles > 0 then round(fare_amount / trip_distance_miles, 2) else null end as cost_per_mile
from trips
