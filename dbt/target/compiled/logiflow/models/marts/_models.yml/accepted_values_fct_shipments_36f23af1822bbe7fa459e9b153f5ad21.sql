
    
    

with all_values as (

    select
        delivery_status as value_field,
        count(*) as n_records

    from LOGIFLOW.DBT_DEV.fct_shipments
    group by delivery_status

)

select *
from all_values
where value_field not in (
    'Advance shipping','Late delivery','Shipping canceled','Shipping on time'
)


