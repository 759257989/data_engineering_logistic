with items as (
    select * from LOGIFLOW.DBT_DEV.stg_dataco__order_items
)
select
    order_item_id,                                                              -- 主键
    md5(cast(coalesce(cast(customer_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))        as customer_key,    -- 外键 -> dim_customers
    md5(cast(coalesce(cast(product_card_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))    as product_key,     -- 外键 -> dim_products
    md5(cast(coalesce(cast(cast(order_ts as date) as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as order_date_key, -- 外键 -> dim_date
    order_id,
    order_ts,
    sales,            -- 以下都是"度量":可以加总、求平均
    quantity,
    discount,
    order_profit
from items