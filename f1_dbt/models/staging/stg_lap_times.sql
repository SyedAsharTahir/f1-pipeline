select
    nullif("raceId",'\N')::int as race_id,
    nullif("driverId",'\N')::int as driver_id,
    nullif("lap",'\N')::int as lap,
    nullif("position",'\N')::int as lap_position,
    nullif("time",'\N') as lap_time,
    nullif("milliseconds",'\N')::int as lap_milliseconds
from {{source('raw','lap_times')}}