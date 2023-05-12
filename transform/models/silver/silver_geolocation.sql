{{ config(unique_key='geolocation_zip_code_prefix') }}

with ranked as (
    select
        *,
        row_number() over (
            partition by geolocation_zip_code_prefix
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_geolocation') }}
    where geolocation_zip_code_prefix is not null
    {{ incremental_updated_at() }}
)

select
    geolocation_zip_code_prefix,
    geolocation_lat,
    geolocation_lng,
    lower(trim(geolocation_city)) as geolocation_city,
    upper(trim(geolocation_state)) as geolocation_state,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
