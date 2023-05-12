select
    cast(order_id as varchar) as order_id,
    try_cast(payment_sequential as integer) as payment_sequential,
    cast(payment_type as varchar) as payment_type,
    try_cast(payment_installments as integer) as payment_installments,
    try_cast(payment_value as double) as payment_value,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('order_payments') }}
