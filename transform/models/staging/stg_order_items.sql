select
    cast(order_id as {{ type_varchar(32) }}) as order_id,
    try_cast(order_item_id as {{ dbt.type_int() }}) as order_item_id,
    cast(product_id as {{ type_varchar(32) }}) as product_id,
    cast(seller_id as {{ type_varchar(32) }}) as seller_id,
    try_cast(shipping_limit_date as {{ dbt.type_timestamp() }}) as shipping_limit_date,
    try_cast(price as {{ type_double() }}) as price,
    try_cast(freight_value as {{ type_double() }}) as freight_value,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('order_items') }}
