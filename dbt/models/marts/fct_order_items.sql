with items as (
    select * from {{ ref('stg_dataco__order_items') }}
)
select
    order_item_id,                                                              -- 主键
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }}        as customer_key,    -- 外键 -> dim_customers
    {{ dbt_utils.generate_surrogate_key(['product_card_id']) }}    as product_key,     -- 外键 -> dim_products
    {{ dbt_utils.generate_surrogate_key(['cast(order_ts as date)']) }} as order_date_key, -- 外键 -> dim_date
    order_id,
    order_ts,
    sales,            -- 以下都是"度量":可以加总、求平均
    quantity,
    discount,
    order_profit
from items