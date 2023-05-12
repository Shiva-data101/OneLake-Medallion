{{ config(materialized='table') }}

select
    items.date_key,
    items.order_date,
    count(distinct items.order_id) as order_count,
    count(*) as order_item_count,
    sum(items.price) as revenue,
    sum(items.freight_value) as freight_amount,
    sum(items.gross_amount) as gross_amount,
    case
        when count(distinct items.order_id) = 0 then 0
        else sum(items.price) / count(distinct items.order_id)
    end as average_order_value,
    count(distinct items.customer_unique_id) as customer_count,
    sum(case when items.order_status = 'canceled' then 1 else 0 end) as canceled_item_count
from {{ ref('fct_order_items') }} as items
group by items.date_key, items.order_date
