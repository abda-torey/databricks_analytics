{{ config(materialized='view') }}

with source as (
    select * from {{ source('bronze_clickstream', 'raw_web_events') }}
),

renamed as (
    select
        -- Identifiers
        cast(event_id as string) as event_id,
        cast(session_id as string) as session_id,
        cast(user_id as string) as user_id,
        cast(anonymous_id as string) as anonymous_id,

        -- Event Attributes
        cast(event_type as string) as event_type,
        cast(page_url as string) as page_url,
        cast(referrer_url as string) as referrer_url,
        cast(search_query as string) as search_query,

        -- Device Context
        cast(device_type as string) as device_type,
        cast(browser as string) as browser,
        cast(os as string) as os,

        -- Location Context
        cast(country as string) as country,
        cast(city as string) as city,

        -- Product Context (Populated conditionally based on Event Type)
        cast(product_id as string) as product_id,
        cast(product_name as string) as product_name,
        cast(product_category as string) as product_category,
        cast(product_price as decimal(10, 2)) as product_price,
        cast(quantity as integer) as quantity,
        cast(revenue as decimal(10, 2)) as revenue,

        -- Timestamps (Strips the trailing 'Z' if needed and converts to true Timestamp)
        to_timestamp(event_timestamp) as event_at
    from source
    where event_id is not null
)

select * from renamed