{# DuckDB FLOAT is 32-bit. dbt.type_float() would quietly shrink price
   and freight on dev. T-SQL float with no precision is float(53). #}
{% macro type_double() %}
{%- if target.type == 'fabric' -%}
float
{%- else -%}
double
{%- endif -%}
{% endmacro %}


{# Fabric wants a length. DuckDB accepts varchar(n) and does not enforce
   it. I set each length from the warehouse, not a blanket 8000. #}
{% macro type_varchar(n) %}
varchar({{ n }})
{% endmacro %}


{# T-SQL has no boolean column. Flags are bit on Fabric, int on DuckDB. #}
{% macro type_flag() %}
{%- if target.type == 'fabric' -%}
bit
{%- else -%}
{{ dbt.type_int() }}
{%- endif -%}
{% endmacro %}
