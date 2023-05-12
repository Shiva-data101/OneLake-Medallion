{{ config(materialized='table') }}

select
    product_id as product_sk,
    product_id,
    product_category_name,
    coalesce(product_category_name_english, product_category_name, 'unknown') as product_category,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    updated_at
from {{ ref('silver_products') }}
