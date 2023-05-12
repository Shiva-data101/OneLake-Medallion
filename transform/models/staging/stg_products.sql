select
    cast(product_id as varchar) as product_id,
    cast(product_category_name as varchar) as product_category_name,
    try_cast(product_name_lenght as integer) as product_name_length,
    try_cast(product_description_lenght as integer) as product_description_length,
    try_cast(product_photos_qty as integer) as product_photos_qty,
    try_cast(product_weight_g as double) as product_weight_g,
    try_cast(product_length_cm as double) as product_length_cm,
    try_cast(product_height_cm as double) as product_height_cm,
    try_cast(product_width_cm as double) as product_width_cm,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('products') }}
