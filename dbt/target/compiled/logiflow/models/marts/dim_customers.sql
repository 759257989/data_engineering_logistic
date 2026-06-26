with ranked as (
    select
        customer_id,
        customer_segment,
        customer_city,
        customer_state,
        customer_country,
        -- 一个客户在源数据里出现很多次(每个订单行一次),
        -- 用 row_number 给每个客户只挑一行(取最近一单的信息)
        row_number() over (partition by customer_id order by order_ts desc) as rn
    from LOGIFLOW.DBT_DEV.stg_dataco__order_items
)
select
    md5(cast(coalesce(cast(customer_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as customer_key,  -- 代理键
    customer_id,
    customer_segment,
    customer_city,
    customer_state,
    customer_country
from ranked
where rn = 1     -- 每个客户只保留一行,保证粒度=一个客户