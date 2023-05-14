{{ config(unique_key='product_id') }}

with ranked as (
    select
        products.*,
        translation.product_category_name_english,
        row_number() over (
            partition by products.product_id
            order by products.updated_at desc, products._ingested_at desc
        ) as _row_num
    from {{ ref('stg_products') }} as products
    left join {{ ref('stg_product_category_translation') }} as translation
        on products.product_category_name = translation.product_category_name
    where products.product_id is not null
    {{ incremental_ingested_at('products._ingested_at') }}
)

select
    product_id,
    product_category_name,
    product_category_name_english,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
