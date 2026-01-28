{{
    config(
        materialized='table',
        unique_key=['country', 'state', 'city', 'brewery_type']
    )
}}

/*
    Gold Layer: Aggregated view of breweries by type and location.

    Business Logic:
    - Groups breweries by type (micro, brewpub, etc.) and location (country, state, city)
    - Calculates brewery counts and quality metrics per group
    - Provides analytical aggregations for business intelligence

    Grain: One row per unique combination of brewery_type + country + state + city
*/

with breweries as (
    select * from {{ ref('stg_breweries') }}
),

aggregated as (
    select
        country,
        state,
        city,
        brewery_type,

        -- Primary metric: count of breweries
        count(*) as total_breweries,

        -- Additional quality metrics
        sum(case when has_coordinates then 1 else 0 end) as breweries_with_coordinates,
        sum(case when has_website then 1 else 0 end) as breweries_with_website,

        -- Average data quality score
        round(avg(data_quality_score)::numeric, 2) as avg_data_quality_score,

        -- Metadata
        current_timestamp as last_updated

    from breweries
    group by
        country,
        state,
        city,
        brewery_type
)

select * from aggregated
order by
    country,
    state,
    city,
    brewery_type
