select
    nullif("raceId",'\N')::int as race_id,
    nullif("driverId",'\N')::int as driver_id,
    nullif("stop",'\N')::int as stop_number,
    nullif("lap",'\N')::int as lap,
    nullif("time",'\N')::time  as pit_time,
    nullif("duration",'\N') as pit_duration,
    nullif("milliseconds",'\N')::int  as pit_milliseconds
from {{source('raw','pit_stops')}}