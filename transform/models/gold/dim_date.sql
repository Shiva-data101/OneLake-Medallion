{{ config(materialized='table') }}

with bounds as (
    select
        min(order_date) as start_date,
        max(order_date) as end_date
    from {{ ref('silver_orders') }}
),

spine as (
    select cast(unnest(generate_series(start_date, end_date, interval '1 day')) as date) as date_day
    from bounds
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    date_day as date_actual,
    extract(year from date_day) as year_number,
    extract(quarter from date_day) as quarter_number,
    extract(month from date_day) as month_number,
    extract(week from date_day) as week_number,
    extract(day from date_day) as day_of_month,
    strftime(date_day, '%A') as day_name,
    strftime(date_day, '%B') as month_name,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from spine
