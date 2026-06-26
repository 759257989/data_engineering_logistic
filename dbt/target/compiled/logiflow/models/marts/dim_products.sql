with ranked as (
    select
        product_card_id,
        product_name,
        category_id,
        category_name,
        row_number() over (partition by product_card_id order by order_ts desc) as rn
    from LOGIFLOW.DBT_DEV.stg_dataco__order_items
)
select
    md5(cast(coalesce(cast(product_card_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as product_key,
    product_card_id,
    product_name,
    category_id,
    category_name
from ranked
where rn = 1