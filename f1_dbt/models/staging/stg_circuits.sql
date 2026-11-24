select
    nullif("circuitId",'\N')::int as circuit_id,
    nullif("circuitRef",'\N') as circuit_ref,
    nullif("name",'\N') as circuit_name,
    nullif("location",'\N') as location,
    nullif("country",'\N') as country,
    nullif("lat",'\N')::numeric as latitude,
    nullif("lng",'\N')::numeric  as longitude,
    nullif("alt",'\N')::numeric as altitude_m,
    nullif("url",'\N') as url
from {{source('raw','circuits')}}