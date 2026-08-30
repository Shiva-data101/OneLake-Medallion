-- Gold gross_amount is what a finance report would sum. If it drifts
-- from price + freight, daily revenue no longer matches the item grain.
select
    order_item_key,
    price,
    freight_value,
    gross_amount
from {{ ref('fct_order_items') }}
where abs((price + freight_value) - gross_amount) > 0.0001
