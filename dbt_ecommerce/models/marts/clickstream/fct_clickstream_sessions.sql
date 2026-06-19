{{ config(
    materialized='table',
    file_format='delta'
) }}

with events as (
    select * from {{ ref('stg_clickstream__events') }}
),

session_aggregates as (
    select
        session_id,
        user_id,
        min(event_at) as session_started_at,
        max(event_at) as session_ended_at,
        
        -- Event counts
        count(event_id) as total_events,
        count(case when event_type = 'page_view' then 1 end) as page_views_count,
        count(case when event_type = 'purchase' then 1 end) as purchases_count,
        
        -- E-commerce conversion metric metrics
        coalesce(sum(revenue), 0.00) as total_session_revenue,
        
        -- Geographies (picks first entry)
        first(country) as session_country,
        first(device_type) as session_device
    from events
    group by session_id, user_id
)

select
    *,
    -- Calculate duration in seconds
    unix_timestamp(session_ended_at) - unix_timestamp(session_started_at) as session_duration_seconds
from session_aggregates