{{
    config(
        materialized='view'
    )
}}

/*
    Staging layer for breweries data from Silver layer.

    This model:
    - Selects relevant columns from source breweries_silver.tb_breweries
    - Ensures data types are consistent
    - Provides a clean interface for downstream marts
*/

with source_data as (
    select
        id,
        name,
        brewery_type,
        city,
        state,
        country,
        longitude,
        latitude,
        has_coordinates,
        phone,
        website_url,
        has_website,
        data_quality_score,
        processed_timestamp,
        source_date
    from {{ source('silver', 'tb_breweries') }}
),

cleaned_data as (
    select
        id,
        name,
        brewery_type,

        -- Location fields
        city,
        state,
        country,

        -- Coordinates
        longitude,
        latitude,
        has_coordinates,

        -- Contact info
        phone,
        website_url,
        has_website,

        -- Quality metrics
        data_quality_score,

        -- Metadata
        processed_timestamp,
        source_date

    from source_data
    where brewery_type is not null
        and city is not null
        and state is not null
        and country is not null
)

select * from cleaned_data
