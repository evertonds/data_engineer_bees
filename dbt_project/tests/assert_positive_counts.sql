/*
    Custom test: Assert that all brewery counts are positive (>= 1)

    This test ensures data integrity by verifying that every aggregated
    row in the gold layer has at least one brewery.

    If this test fails, it indicates a logic error in the aggregation.
*/

select
    country,
    state,
    city,
    brewery_type,
    brewery_count
from {{ ref('breweries_by_type_location') }}
where brewery_count < 1
    or brewery_count is null
