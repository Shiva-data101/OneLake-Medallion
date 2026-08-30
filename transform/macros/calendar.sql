{# Days since Sunday 1900-01-07, mod 7. 0=Sunday .. 6=Saturday.
   Independent of SET DATEFIRST and session language. #}
{% macro weekday_sun0(date_expr) %}
({{ dbt.datediff("cast('1900-01-07' as date)", date_expr, "day") }} % 7)
{% endmacro %}


{% macro date_part_quarter(date_expr) %}
{%- if target.type == 'fabric' -%}
datepart(quarter, {{ date_expr }})
{%- else -%}
quarter({{ date_expr }})
{%- endif -%}
{% endmacro %}


{# ISO week on both engines. DATEPART(week) is DATEFIRST-dependent. #}
{% macro date_part_week(date_expr) %}
{%- if target.type == 'fabric' -%}
datepart(iso_week, {{ date_expr }})
{%- else -%}
week({{ date_expr }})
{%- endif -%}
{% endmacro %}
