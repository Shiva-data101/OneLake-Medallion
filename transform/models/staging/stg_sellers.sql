select
    cast(seller_id as {{ type_varchar(32) }}) as seller_id,
    cast(seller_zip_code_prefix as {{ type_varchar(5) }}) as seller_zip_code_prefix,
    cast(seller_city as {{ type_varchar(64) }}) as seller_city,
    cast(seller_state as {{ type_varchar(2) }}) as seller_state,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('sellers') }}
