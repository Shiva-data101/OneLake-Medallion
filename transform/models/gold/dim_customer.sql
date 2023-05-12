{{ config(materialized='table') }}

with latest as (
    select
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        updated_at,
        row_number() over (
            partition by customer_unique_id
            order by updated_at desc
        ) as _row_num
    from {{ ref('silver_customers') }}
)

select
    customer_unique_id as customer_sk,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    updated_at
from latest
where _row_num = 1
