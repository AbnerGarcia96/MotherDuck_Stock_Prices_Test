{#
    Use the custom schema (silver/gold) as-is instead of dbt's default
    "<target_schema>_<custom_schema>" concatenation, so models land in
    silver.* / gold.* the same way the Flights they replace did.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
