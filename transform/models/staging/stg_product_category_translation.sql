select
    cast(product_category_name as {{ type_varchar(64) }}) as product_category_name,
    cast(product_category_name_english as {{ type_varchar(64) }}) as product_category_name_english,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('product_category_translation') }}
