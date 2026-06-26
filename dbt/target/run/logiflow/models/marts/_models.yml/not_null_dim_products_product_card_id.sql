
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_card_id
from LOGIFLOW.DBT_DEV.dim_products
where product_card_id is null



  
  
      
    ) dbt_internal_test