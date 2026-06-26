select
    {{ dbt_utils.generate_surrogate_key(['location_id']) }} as zone_key,
    location_id,
    borough,
    zone,
    service_zone
from {{ ref('stg_taxi__zones') }}