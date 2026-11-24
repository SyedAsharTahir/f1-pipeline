select
    circuit_id,
    circuit_ref,
    circuit_name,
    location,
    country,
    latitude,
    longitude,
    altitude_m,
    url
from {{ref('stg_circuits')}}