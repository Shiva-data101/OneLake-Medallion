select
    cast(review_id as varchar) as review_id,
    cast(order_id as varchar) as order_id,
    try_cast(review_score as integer) as review_score,
    cast(review_comment_title as varchar) as review_comment_title,
    cast(review_comment_message as varchar) as review_comment_message,
    try_cast(review_creation_date as timestamp) as review_creation_date,
    try_cast(review_answer_timestamp as timestamp) as review_answer_timestamp,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as timestamp) as updated_at,
    try_cast(_ingested_at as timestamp) as _ingested_at,
    cast(_source_file as varchar) as _source_file,
    cast(_batch_id as varchar) as _batch_id
from {{ bronze_source('order_reviews') }}
