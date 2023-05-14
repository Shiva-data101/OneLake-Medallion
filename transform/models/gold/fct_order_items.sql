{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        incremental_strategy='delete+insert'
    )
}}

select
    items.order_item_key,
    items.order_id,
    items.order_item_id,
    orders.customer_id,
    customers.customer_unique_id,
    customers.customer_unique_id as customer_sk,
    items.product_id,
    items.product_id as product_sk,
    items.seller_id,
    orders.order_status,
    items.order_date,
    cast(strftime(items.order_date, '%Y%m%d') as integer) as date_key,
    orders.order_purchase_timestamp,
    items.price,
    items.freight_value,
    items.price + items.freight_value as gross_amount,
    items.updated_at,
    items._ingested_at
from {{ ref('silver_order_items') }} as items
inner join {{ ref('silver_orders') }} as orders
    on items.order_id = orders.order_id
left join {{ ref('silver_customers') }} as customers
    on orders.customer_id = customers.customer_id
where not items.is_quarantined
  and items.price >= 0
  and items.freight_value >= 0
{% if is_incremental() %}
  and items._ingested_at > (
      select coalesce(max(_ingested_at), timestamp '1900-01-01 00:00:00')
      from {{ this }}
  )
{% endif %}
