
    
    

with child as (
    select customer_key as from_field
    from LOGIFLOW.DBT_DEV.fct_order_items
    where customer_key is not null
),

parent as (
    select customer_key as to_field
    from LOGIFLOW.DBT_DEV.dim_customers
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


