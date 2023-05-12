{{ config(unique_key='order_item_key') }}

with ranked as (
    select
        *,
        order_id || '-' || cast(order_item_id as varchar) as order_item_key,
        row_number() over (
            partition by order_id, order_item_id
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_order_items') }}
    where order_id is not null
      and order_item_id is not null
      and product_id is not null
    {{ incremental_updated_at() }}
)

select
    order_item_key,
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value,
    order_date,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id,
    case
        when price < 0 or freight_value < 0 then true
        else false
    end as is_quarantined
from ranked
where _row_num = 1
