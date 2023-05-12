select
    cast(order_id as varchar) as order_id,
    cast(customer_id as varchar) as customer_id,
    cast(order_status as varchar) as order_status,
    try_cast(order_purchase_timestamp as timestamp) as order_purchase_timestamp,
    try_cast(order_approved_at as timestamp) as order_approved_at,
    try_cast(order_delivered_carrier_date as timestamp) as order_delivered_carrier_date,
    try_cast(order_delivered_customer_date as timestamp) as order_delivered_customer_date,
    try_cast(order_estimated_delivery_date as timestamp) as order_estimated_delivery_date,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('orders') }}
