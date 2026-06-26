
  
    

create or replace transient table LOGIFLOW.DBT_DEV.dim_date
    
    
    
    as (with spine as (
    -- date_spine 宏:自动生成一段连续日期(这里 2015 到 2026,够覆盖订单和行程)
    





with rawdata as (

    

    

    with p as (
        select 0 as generated_number union all select 1
    ), unioned as (

    select

    
    p0.generated_number * power(2, 0)
     + 
    
    p1.generated_number * power(2, 1)
     + 
    
    p2.generated_number * power(2, 2)
     + 
    
    p3.generated_number * power(2, 3)
     + 
    
    p4.generated_number * power(2, 4)
     + 
    
    p5.generated_number * power(2, 5)
     + 
    
    p6.generated_number * power(2, 6)
     + 
    
    p7.generated_number * power(2, 7)
     + 
    
    p8.generated_number * power(2, 8)
     + 
    
    p9.generated_number * power(2, 9)
     + 
    
    p10.generated_number * power(2, 10)
     + 
    
    p11.generated_number * power(2, 11)
    
    
    + 1
    as generated_number

    from

    
    p as p0
     cross join 
    
    p as p1
     cross join 
    
    p as p2
     cross join 
    
    p as p3
     cross join 
    
    p as p4
     cross join 
    
    p as p5
     cross join 
    
    p as p6
     cross join 
    
    p as p7
     cross join 
    
    p as p8
     cross join 
    
    p as p9
     cross join 
    
    p as p10
     cross join 
    
    p as p11
    
    

    )

    select *
    from unioned
    where generated_number <= 4018
    order by generated_number



),

all_periods as (

    select (
        

    dateadd(
        day,
        row_number() over (order by generated_number) - 1,
        cast('2015-01-01' as date)
        )


    ) as date_day
    from rawdata

),

filtered as (

    select *
    from all_periods
    where date_day <= cast('2026-01-01' as date)

)

select * from filtered


)
select
    md5(cast(coalesce(cast(cast(date_day as date) as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as date_key,
    cast(date_day as date)        as date_day,
    year(date_day)                as year,
    quarter(date_day)             as quarter,
    month(date_day)               as month,
    monthname(date_day)           as month_name,
    day(date_day)                 as day_of_month,
    dayofweek(date_day)           as day_of_week,
    case when dayofweek(date_day) in (0, 6) then true else false end as is_weekend
from spine
    )
;


  