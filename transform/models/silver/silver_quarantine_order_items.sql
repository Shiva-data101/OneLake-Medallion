{{ config(materialized='table', unique_key='order_item_key') }}

select *
from {{ ref('silver_order_items') }}
where is_quarantined
   or price is null
   or freight_value is null
