{{ config(unique_key='order_id') }}

with ranked as (
    select
        *,
        row_number() over (
            partition by order_id
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_orders') }}
    where order_id is not null
    {{ incremental_ingested_at() }}
)

select
    order_id,
    customer_id,
    lower(trim(order_status)) as order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    coalesce(order_date, cast(order_purchase_timestamp as date)) as order_date,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
