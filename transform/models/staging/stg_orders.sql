select
    cast(order_id as {{ type_varchar(32) }}) as order_id,
    cast(customer_id as {{ type_varchar(32) }}) as customer_id,
    cast(order_status as {{ type_varchar(16) }}) as order_status,
    try_cast(order_purchase_timestamp as {{ dbt.type_timestamp() }}) as order_purchase_timestamp,
    try_cast(order_approved_at as {{ dbt.type_timestamp() }}) as order_approved_at,
    try_cast(order_delivered_carrier_date as {{ dbt.type_timestamp() }}) as order_delivered_carrier_date,
    try_cast(order_delivered_customer_date as {{ dbt.type_timestamp() }}) as order_delivered_customer_date,
    try_cast(order_estimated_delivery_date as {{ dbt.type_timestamp() }}) as order_estimated_delivery_date,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('orders') }}
