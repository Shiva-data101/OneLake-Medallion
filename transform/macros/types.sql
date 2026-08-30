{# DuckDB FLOAT is single-precision. dbt.type_float() would silently
   degrade price/freight on dev. T-SQL float without precision is float(53). #}
{% macro type_double() %}
{%- if target.type == 'fabric' -%}
float
{%- else -%}
double
{%- endif -%}
{% endmacro %}


{# Fabric requires an explicit length. DuckDB accepts varchar(n) and does
   not enforce it. Lengths are set per column from measured warehouse values. #}
{% macro type_varchar(n) %}
varchar({{ n }})
{% endmacro %}


{# T-SQL has no boolean column type. Flags are bit on Fabric, int on DuckDB. #}
{% macro type_flag() %}
{%- if target.type == 'fabric' -%}
bit
{%- else -%}
{{ dbt.type_int() }}
{%- endif -%}
{% endmacro %}
