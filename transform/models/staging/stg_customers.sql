select
    cast(customer_id as {{ type_varchar(32) }}) as customer_id,
    cast(customer_unique_id as {{ type_varchar(32) }}) as customer_unique_id,
    cast(customer_zip_code_prefix as {{ type_varchar(5) }}) as customer_zip_code_prefix,
    cast(customer_city as {{ type_varchar(64) }}) as customer_city,
    cast(customer_state as {{ type_varchar(2) }}) as customer_state,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('customers') }}
