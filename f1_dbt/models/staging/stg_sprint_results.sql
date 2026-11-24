select
    nullif("resultId",'\N')::int as sprint_result_id,
    nullif("raceId",'\N')::int as race_id,
    nullif("driverId",'\N')::int as driver_id,
    nullif("constructorId",'\N')::int as constructor_id,
    nullif("number",'\N')::int as car_number,
    nullif("grid",'\N')::int as grid_position,
    nullif("position",'\N')::int  as finish_position,
    nullif("positionText",'\N') as position_text,
    nullif("positionOrder",'\N')::int as position_order,
    nullif("points",'\N')::numeric as points,
    nullif("laps",'\N')::int as laps_completed,
    nullif("time",'\N') as finish_time,
    nullif("milliseconds",'\N')::int as finish_milliseconds,
    nullif("fastestLap",'\N')::int as fastest_lap_number,
    nullif("fastestLapTime",'\N') as fastest_lap_time,
    nullif("statusId",'\N')::int as status_id
from {{source('raw','sprint_results')}}