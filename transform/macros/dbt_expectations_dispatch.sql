{# All nine Fabric dbt_expectations errors share one path:
     expect_* -> expression_is_true -> truth_expression
   default__truth_expression selects a boolean column and then filters
   `not(expression = true)`. T-SQL has neither. These overrides keep
   three-valued logic (NULL stays NULL, not a failure) on DuckDB and Fabric. #}

{% macro default__truth_expression(expression) %}
case
    when ({{ expression }}) then 1
    when not ({{ expression }}) then 0
end as expression
{% endmacro %}


{% macro default__expression_is_true(model, expression, test_condition, group_by_columns, row_condition) -%}
{%- set test_condition = "= 1" if test_condition == "= true" else test_condition -%}
with grouped_expression as (
    select
        {% if group_by_columns %}
        {% for group_by_column in group_by_columns -%}
        {{ group_by_column }} as col_{{ loop.index }},
        {% endfor -%}
        {% endif %}
        {{ dbt_expectations.truth_expression(expression) }}
    from {{ model }}
     {%- if row_condition %}
    where
        {{ row_condition }}
    {% endif %}
    {% if group_by_columns %}
    group by
    {% for group_by_column in group_by_columns -%}
        {{ group_by_column }}{% if not loop.last %},{% endif %}
    {% endfor %}
    {% endif %}

),
validation_errors as (

    select
        *
    from
        grouped_expression
    where
        not(expression {{ test_condition }})

)

select *
from validation_errors

{% endmacro -%}
