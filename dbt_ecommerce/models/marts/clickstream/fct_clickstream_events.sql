{{ config(
    materialized='incremental',
    unique_key='event_id',
    file_format='delta',
    liquid_clustering=['event_type', 'event_date']
) }}

with staged_events as (
    select * from {{ ref('stg_clickstream__events') }}
    {% if is_incremental() %}
      -- Only process data that arrived since the last run
      where event_at >= (select max(event_at) - interval 3 hours from {{ this }})
    {% endif %}
)

select
    *,
    cast(event_at as date) as event_date
from staged_events