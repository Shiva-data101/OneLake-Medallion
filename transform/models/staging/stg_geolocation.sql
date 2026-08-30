select
    cast(geolocation_zip_code_prefix as {{ type_varchar(5) }}) as geolocation_zip_code_prefix,
    try_cast(geolocation_lat as {{ type_double() }}) as geolocation_lat,
    try_cast(geolocation_lng as {{ type_double() }}) as geolocation_lng,
    cast(geolocation_city as {{ type_varchar(64) }}) as geolocation_city,
    cast(geolocation_state as {{ type_varchar(2) }}) as geolocation_state,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('geolocation') }}
