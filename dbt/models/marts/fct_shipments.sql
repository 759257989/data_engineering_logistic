with ranked as (
    select
        order_id,
        customer_id,
        order_ts,
        shipping_ts,
        days_shipping_real,
        days_shipping_scheduled,
        delivery_status,
        late_delivery_risk,
        shipping_mode,
        -- 发货相关字段在"订单"粒度上是一致的,每个订单挑一行即可
        row_number() over (partition by order_id order by order_item_id) as rn
    from {{ ref('stg_dataco__order_items') }}
)
select
    order_id,
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }}        as customer_key,
    {{ dbt_utils.generate_surrogate_key(['cast(order_ts as date)']) }} as order_date_key,
    order_ts,
    shipping_ts,
    days_shipping_real,
    days_shipping_scheduled,
    (days_shipping_real - days_shipping_scheduled) as delay_days,   -- 实际比计划多花几天
    case when days_shipping_real > days_shipping_scheduled then true else false end as is_late,
    delivery_status,
    late_delivery_risk,
    shipping_mode
from ranked
where rn = 1