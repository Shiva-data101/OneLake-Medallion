{# Days since Sunday 1900-01-07, mod 7. 0=Sunday to 6=Saturday.
   Does not depend on SET DATEFIRST or session language. #}
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


{# ISO week on both engines. DATEPART(week) changes with DATEFIRST. #}
{% macro date_part_week(date_expr) %}
{%- if target.type == 'fabric' -%}
datepart(iso_week, {{ date_expr }})
{%- else -%}
week({{ date_expr }})
{%- endif -%}
{% endmacro %}
