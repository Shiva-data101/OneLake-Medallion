{% macro bronze_source(table_name) %}
{%- set root = env_var('ONELAKE_BRONZE', 'data/bronze') -%}
read_parquet('{{ root }}/{{ table_name }}/*.parquet', union_by_name=true, hive_partitioning=0)
{% endmacro %}


{% macro incremental_updated_at(column_name='updated_at') %}
{% if is_incremental() %}
and {{ column_name }} > (
    select coalesce(max(updated_at), timestamp '1900-01-01 00:00:00')
    from {{ this }}
)
{% endif %}
{% endmacro %}
