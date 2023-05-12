select
    cast(seller_id as varchar) as seller_id,
    cast(seller_zip_code_prefix as varchar) as seller_zip_code_prefix,
    cast(seller_city as varchar) as seller_city,
    cast(seller_state as varchar) as seller_state,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('sellers') }}
