{% macro bronze_source(table_name) %}
{%- if var('ci_mode', false) -%}
{{ ref(table_name ~ '_seed') }}
{%- else -%}
{%- set root = env_var('ONELAKE_BRONZE', 'data/bronze') -%}
read_parquet('{{ root }}/{{ table_name }}/*.parquet', union_by_name=true, hive_partitioning=0)
{%- endif -%}
{% endmacro %}


{# Arrival clock, not business clock. updated_at can sit in the future after
   backfill (delivery dates); _ingested_at only moves when ingest writes. #}
{% macro incremental_ingested_at(column_name='_ingested_at') %}
{% if is_incremental() %}
and {{ column_name }} > (
    select coalesce(max(_ingested_at), timestamp '1900-01-01 00:00:00')
    from {{ this }}
)
{% endif %}
{% endmacro %}
