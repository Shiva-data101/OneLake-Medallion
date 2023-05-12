select
    cast(geolocation_zip_code_prefix as varchar) as geolocation_zip_code_prefix,
    try_cast(geolocation_lat as double) as geolocation_lat,
    try_cast(geolocation_lng as double) as geolocation_lng,
    cast(geolocation_city as varchar) as geolocation_city,
    cast(geolocation_state as varchar) as geolocation_state,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('geolocation') }}
