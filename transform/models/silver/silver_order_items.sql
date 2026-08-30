{{ config(unique_key='order_item_key') }}

with ranked as (
    select
        *,
        {{ dbt.concat([
            'order_id',
            "'-'",
            'cast(order_item_id as ' ~ type_varchar(8) ~ ')'
        ]) }} as order_item_key,
        row_number() over (
            partition by order_id, order_item_id
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_order_items') }}
    where order_id is not null
      and order_item_id is not null
      and product_id is not null
    {{ incremental_ingested_at() }}
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
    cast(
        case when price < 0 or freight_value < 0 then 1 else 0 end
        as {{ type_flag() }}
    ) as is_quarantined
from ranked
where _row_num = 1
