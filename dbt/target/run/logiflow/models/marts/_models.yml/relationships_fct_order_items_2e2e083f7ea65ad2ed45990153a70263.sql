
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select product_key as from_field
    from LOGIFLOW.DBT_DEV.fct_order_items
    where product_key is not null
),

parent as (
    select product_key as to_field
    from LOGIFLOW.DBT_DEV.dim_products
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test