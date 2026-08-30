{# dbt_utils.generate_series() ends with ORDER BY, which T-SQL does not
   allow in a CTE. The adapter copy is a nested WITH, and Fabric CTAS
   fails with "Get single node from XML DOM failed". This one is a plain SELECT. #}
{% macro fabric__generate_series(upper_bound) %}
    {% if upper_bound <= 0 %}
        {{ exceptions.raise_compiler_error("upper bound must be positive") }}
    {% endif %}

    {% set ns = namespace(powers_of_two=none) %}
    {% for _ in range(1, 100) %}
        {% if ns.powers_of_two is none and upper_bound <= 2 ** loop.index %}
            {% set ns.powers_of_two = loop.index %}
        {% endif %}
    {% endfor %}

    {% if ns.powers_of_two is none %}
        {{ exceptions.raise_compiler_error("upper bound must be <= 2 ** 99 (got " ~ upper_bound ~ ")") }}
    {% endif %}

    select
        {% for i in range(ns.powers_of_two) %}
        p{{ i }}.generated_number * power(2, {{ i }})
        {% if not loop.last %} + {% endif %}
        {% endfor %}
        + 1 as generated_number
    from
        {% for i in range(ns.powers_of_two) %}
        (select 0 as generated_number union all select 1) as p{{ i }}
        {% if not loop.last %} cross join {% endif %}
        {% endfor %}
    where
        {% for i in range(ns.powers_of_two) %}
        p{{ i }}.generated_number * power(2, {{ i }})
        {% if not loop.last %} + {% endif %}
        {% endfor %}
        + 1 <= {{ upper_bound }}
{% endmacro %}
