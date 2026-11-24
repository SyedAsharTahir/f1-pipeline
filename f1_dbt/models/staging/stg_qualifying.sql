select
    nullif("qualifyId",'\N')::int as qualify_id,
    nullif("raceId",'\N')::int as race_id,
    nullif("driverId",'\N')::int as driver_id,
    nullif("constructorId",'\N')::int as constructor_id,
    nullif("number",'\N')::int as qualify_number,
    nullif("position",'\N')::int as qualifying_position,
    nullif("q1",'\N')  as q1_time,
    nullif("q2",'\N') as q2_time,
    nullif("q3",'\N')as q3_time
from {{source('raw','qualifying')}}