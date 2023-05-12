select
    cast(customer_id as varchar) as customer_id,
    cast(customer_unique_id as varchar) as customer_unique_id,
    cast(customer_zip_code_prefix as varchar) as customer_zip_code_prefix,
    cast(customer_city as varchar) as customer_city,
    cast(customer_state as varchar) as customer_state,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('customers') }}
