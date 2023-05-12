select
    cast(product_category_name as varchar) as product_category_name,
    cast(product_category_name_english as varchar) as product_category_name_english,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('product_category_translation') }}
