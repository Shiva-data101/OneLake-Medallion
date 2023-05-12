{{ config(unique_key='review_id') }}

with ranked as (
    select
        *,
        row_number() over (
            partition by review_id
            order by updated_at desc, _ingested_at desc
        ) as _row_num
    from {{ ref('stg_order_reviews') }}
    where review_id is not null
      and order_id is not null
    {{ incremental_updated_at() }}
)

select
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp,
    order_date,
    updated_at,
    _ingested_at,
    _source_file,
    _batch_id
from ranked
where _row_num = 1
