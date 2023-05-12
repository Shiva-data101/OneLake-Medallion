{{ config(unique_key='payment_key') }}

with ranked as (
    select
        *,
        order_id || '-' || cast(payment_sequential as varchar) as payment_key,
        row_number() over (
            partition by order_id, payment_sequential
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_order_payments') }}
    where order_id is not null
      and payment_sequential is not null
    {{ incremental_updated_at() }}
)

select
    payment_key,
    order_id,
    payment_sequential,
    lower(trim(payment_type)) as payment_type,
    payment_installments,
    payment_value,
    order_date,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
