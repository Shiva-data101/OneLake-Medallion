select
    cast(review_id as {{ type_varchar(32) }}) as review_id,
    cast(order_id as {{ type_varchar(32) }}) as order_id,
    try_cast(review_score as {{ dbt.type_int() }}) as review_score,
    cast(review_comment_title as {{ type_varchar(32) }}) as review_comment_title,
    cast(review_comment_message as {{ type_varchar(256) }}) as review_comment_message,
    try_cast(review_creation_date as {{ dbt.type_timestamp() }}) as review_creation_date,
    try_cast(review_answer_timestamp as {{ dbt.type_timestamp() }}) as review_answer_timestamp,
    try_cast(order_date as date) as order_date,
    try_cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
    try_cast(_ingested_at as {{ dbt.type_timestamp() }}) as _ingested_at,
    cast(_source_file as {{ type_varchar(256) }}) as _source_file,
    cast(_batch_id as {{ type_varchar(36) }}) as _batch_id
from {{ bronze_source('order_reviews') }}
