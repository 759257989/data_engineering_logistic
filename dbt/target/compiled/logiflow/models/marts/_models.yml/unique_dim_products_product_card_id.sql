
    
    

select
    product_card_id as unique_field,
    count(*) as n_records

from LOGIFLOW.DBT_DEV.dim_products
where product_card_id is not null
group by product_card_id
having count(*) > 1


