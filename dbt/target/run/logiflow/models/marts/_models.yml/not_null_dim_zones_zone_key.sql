
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select zone_key
from LOGIFLOW.DBT_DEV.dim_zones
where zone_key is null



  
  
      
    ) dbt_internal_test