
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

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



  
  
      
    ) dbt_internal_test