
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date_day
from LOGIFLOW.DBT_DEV.dim_date
where date_day is null



  
  
      
    ) dbt_internal_test