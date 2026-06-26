
  
    

create or replace transient table LOGIFLOW.DBT_DEV.fct_shipments
    
    
    
    as (with ranked as (
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
    from LOGIFLOW.DBT_DEV.stg_dataco__order_items
)
select
    order_id,
    md5(cast(coalesce(cast(customer_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))        as customer_key,
    md5(cast(coalesce(cast(cast(order_ts as date) as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as order_date_key,
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
    )
;


  