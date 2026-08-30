{# One seam for where bronze lives. Three environments, one macro:
     ci      -> committed seed fixtures
     fabric  -> Delta tables in the lh_bronze Lakehouse, read cross-database
                from the Warehouse (any Warehouse can read any Lakehouse in
                the same workspace via item.schema.table)
     dev     -> local parquet on disk, read by DuckDB #}
{% macro bronze_source(table_name) %}
{%- if var('ci_mode', false) -%}
{{ ref(table_name ~ '_seed') }}
{%- elif target.type == 'fabric' -%}
{%- set lakehouse = var('bronze_lakehouse', 'lh_bronze') -%}
[{{ lakehouse }}].[dbo].[bronze_{{ table_name }}]
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
    select coalesce(
        max(_ingested_at),
        cast('1900-01-01 00:00:00' as {{ dbt.type_timestamp() }})
    )
    from {{ this }}
)
{% endif %}
{% endmacro %}
