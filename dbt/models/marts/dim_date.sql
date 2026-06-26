with spine as (
    -- date_spine 宏:自动生成一段连续日期(这里 2015 到 2026,够覆盖订单和行程)
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2015-01-01' as date)",
        end_date="cast('2026-01-01' as date)"
    ) }}
)
select
    {{ dbt_utils.generate_surrogate_key(['cast(date_day as date)']) }} as date_key,
    cast(date_day as date)        as date_day,
    year(date_day)                as year,
    quarter(date_day)             as quarter,
    month(date_day)               as month,
    monthname(date_day)           as month_name,
    day(date_day)                 as day_of_month,
    dayofweek(date_day)           as day_of_week,
    case when dayofweek(date_day) in (0, 6) then true else false end as is_weekend
from spine