
  create or replace   view LOGIFLOW.DBT_DEV.stg_dataco__order_items
  
  
  
  
  as (
    with source as (
    select * from LOGIFLOW.RAW.dataco_supply_chain
),
renamed as (
    -- 说明:RAW 表由 INFER_SCHEMA 从 Parquet 自动建表,列名是"小写、区分大小写"的,
    -- 必须用双引号 "..." 引用源列;输出别名不加引号,这样下游 marts 用的就是干净的大写列名。
    select
        "order_item_id"                                                      as order_item_id,
        "order_id"                                                          as order_id,
        "customer_id"                                                       as customer_id,
        "product_card_id"                                                   as product_card_id,
        "category_id"                                                       as category_id,
        "category_name"                                                     as category_name,
        -- DataCo 的日期是 '1/31/2018 22:56' 这种字符串,在这里解析成真正的时间戳
        to_timestamp_ntz("order_date_date_orders", 'MM/DD/YYYY HH24:MI')    as order_ts,
        to_timestamp_ntz("shipping_date_date_orders", 'MM/DD/YYYY HH24:MI') as shipping_ts,
        "days_for_shipping_real"::int                                       as days_shipping_real,
        "days_for_shipment_scheduled"::int                                  as days_shipping_scheduled,
        "delivery_status"                                                   as delivery_status,
        "late_delivery_risk"::int                                          as late_delivery_risk,
        "shipping_mode"                                                     as shipping_mode,
        "sales"::float                                                      as sales,
        "order_item_quantity"::int                                         as quantity,
        "order_item_discount"::float                                       as discount,
        "order_profit_per_order"::float                                    as order_profit,
        "customer_segment"                                                  as customer_segment,
        "customer_city"                                                     as customer_city,
        "customer_state"                                                    as customer_state,
        "customer_country"                                                  as customer_country,
        "product_name"                                                      as product_name,
        "market"                                                            as market,
        "order_region"                                                      as order_region,
        "order_country"                                                     as order_country,
        "order_city"                                                        as order_city
        -- 注意:customer_email / customer_password / customer_fname / customer_lname
        -- / customer_street 这些隐私字段(PII)在这里被故意不选,等于在进入分析层前就脱敏
    from source
)
select * from renamed
  );

