select
    cast(product_id as {{ type_varchar(32) }}) as product_id,
    cast(product_category_name as {{ type_varchar(64) }}) as product_category_name,
    try_cast(product_name_lenght as {{ dbt.type_int() }}) as product_name_length,
    try_cast(product_description_lenght as {{ dbt.type_int() }}) as product_description_length,
    try_cast(product_photos_qty as {{ dbt.type_int() }}) as product_photos_qty,
    try_cast(product_weight_g as {{ type_double() }}) as product_weight_g,
    try_cast(product_length_cm as {{ type_double() }}) as product_length_cm,
    try_cast(product_height_cm as {{ type_double() }}) as product_height_cm,
    try_cast(product_width_cm as {{ type_double() }}) as product_width_cm,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('products') }}
