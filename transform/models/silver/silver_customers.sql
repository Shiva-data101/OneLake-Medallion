{{ config(unique_key='customer_id') }}

with ranked as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_customers') }}
    where customer_id is not null
      and customer_unique_id is not null
    {{ incremental_ingested_at() }}
)

select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    lower(trim(customer_city)) as customer_city,
    upper(trim(customer_state)) as customer_state,
    order_date,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
