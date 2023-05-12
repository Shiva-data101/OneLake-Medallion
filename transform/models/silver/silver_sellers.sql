{{ config(unique_key='seller_id') }}

with ranked as (
    select
        *,
        row_number() over (
            partition by seller_id
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_sellers') }}
    where seller_id is not null
    {{ incremental_updated_at() }}
)

select
    seller_id,
    seller_zip_code_prefix,
    lower(trim(seller_city)) as seller_city,
    upper(trim(seller_state)) as seller_state,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
