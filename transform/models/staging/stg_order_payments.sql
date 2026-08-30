select
    cast(order_id as {{ type_varchar(32) }}) as order_id,
    try_cast(payment_sequential as {{ dbt.type_int() }}) as payment_sequential,
    cast(payment_type as {{ type_varchar(16) }}) as payment_type,
    try_cast(payment_installments as {{ dbt.type_int() }}) as payment_installments,
    try_cast(payment_value as {{ type_double() }}) as payment_value,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('order_payments') }}
