
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    product_card_id as unique_field,
    count(*) as n_records

from LOGIFLOW.DBT_DEV.dim_products
where product_card_id is not null
group by product_card_id
having count(*) > 1



  
  
      
    ) dbt_internal_test