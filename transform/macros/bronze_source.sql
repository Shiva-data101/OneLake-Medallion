{# One place that says where bronze lives.
     ci      -> committed seed fixtures
     fabric  -> Delta tables in lh_bronze, read from the Warehouse
                (any Warehouse can read any Lakehouse in the same workspace)
     dev     -> local parquet, read by DuckDB #}
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


{# Do not use updated_at here. It is a delivery date so it can be far in
   the future. _ingested_at only changes when ingest actually writes, so it is safe. #}
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
