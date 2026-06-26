
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

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



  
  
      
    ) dbt_internal_test