with ranked as (
    select
        product_card_id,
        product_name,
        category_id,
        category_name,
        row_number() over (partition by product_card_id order by order_ts desc) as rn
    from {{ ref('stg_dataco__order_items') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['product_card_id']) }} as product_key,
    product_card_id,
    product_name,
    category_id,
    category_name
from ranked
where rn = 1