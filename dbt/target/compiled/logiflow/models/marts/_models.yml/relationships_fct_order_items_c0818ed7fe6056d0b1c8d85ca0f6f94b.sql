
    
    

with child as (
    select order_date_key as from_field
    from LOGIFLOW.DBT_DEV.fct_order_items
    where order_date_key is not null
),

parent as (
    select date_key as to_field
    from LOGIFLOW.DBT_DEV.dim_date
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


