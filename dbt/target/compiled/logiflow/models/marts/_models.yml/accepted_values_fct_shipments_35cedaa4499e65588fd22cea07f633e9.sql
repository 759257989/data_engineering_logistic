
    
    

with all_values as (

    select
        shipping_mode as value_field,
        count(*) as n_records

    from LOGIFLOW.DBT_DEV.fct_shipments
    group by shipping_mode

)

select *
from all_values
where value_field not in (
    'First Class','Same Day','Second Class','Standard Class'
)


