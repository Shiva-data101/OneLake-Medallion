{{ config(materialized='table') }}

with bounds as (
    select
        min(order_date) as start_date,
        max(order_date) as end_date
    from {{ ref('silver_orders') }}
),

spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2019-01-02' as date)"
    ) }}
)

select
    cast(
        year(spine.date_day) * 10000
        + month(spine.date_day) * 100
        + day(spine.date_day)
        as {{ dbt.type_int() }}
    ) as date_key,
    cast(spine.date_day as date) as date_actual,
    year(spine.date_day) as year_number,
    {{ date_part_quarter('spine.date_day') }} as quarter_number,
    month(spine.date_day) as month_number,
    {{ date_part_week('spine.date_day') }} as week_number,
    day(spine.date_day) as day_of_month,
    case {{ weekday_sun0('spine.date_day') }}
        when 0 then 'Sunday'
        when 1 then 'Monday'
        when 2 then 'Tuesday'
        when 3 then 'Wednesday'
        when 4 then 'Thursday'
        when 5 then 'Friday'
        when 6 then 'Saturday'
    end as day_name,
    case month(spine.date_day)
        when 1 then 'January'
        when 2 then 'February'
        when 3 then 'March'
        when 4 then 'April'
        when 5 then 'May'
        when 6 then 'June'
        when 7 then 'July'
        when 8 then 'August'
        when 9 then 'September'
        when 10 then 'October'
        when 11 then 'November'
        when 12 then 'December'
    end as month_name,
    cast(
        case
            when {{ weekday_sun0('spine.date_day') }} in (0, 6) then 1
            else 0
        end
        as {{ type_flag() }}
    ) as is_weekend
from spine
inner join bounds
    on cast(spine.date_day as date) between bounds.start_date and bounds.end_date
