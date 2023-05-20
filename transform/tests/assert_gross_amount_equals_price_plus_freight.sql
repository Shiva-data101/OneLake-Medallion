-- Gold gross_amount is the line a finance report would sum. If the
-- expression drifts from price + freight, daily revenue splits from
-- the item grain without anyone noticing.
select
    order_item_key,
    price,
    freight_value,
    gross_amount
from {{ ref('fct_order_items') }}
where abs((price + freight_value) - gross_amount) > 0.0001
