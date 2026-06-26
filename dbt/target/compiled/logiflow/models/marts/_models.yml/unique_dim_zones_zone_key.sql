
    
    

select
    zone_key as unique_field,
    count(*) as n_records

from LOGIFLOW.DBT_DEV.dim_zones
where zone_key is not null
group by zone_key
having count(*) > 1


