select
    cast(order_id as varchar) as order_id,
    try_cast(order_item_id as integer) as order_item_id,
    cast(product_id as varchar) as product_id,
    cast(seller_id as varchar) as seller_id,
    try_cast(shipping_limit_date as timestamp) as shipping_limit_date,
    try_cast(price as double) as price,
    try_cast(freight_value as double) as freight_value,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('order_items') }}
