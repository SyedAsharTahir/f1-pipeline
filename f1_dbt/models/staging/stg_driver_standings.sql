select
    nullif("driverStandingsId",'\N')::int as driver_standings_id,
    nullif("raceId",'\N')::int as race_id,
    nullif("driverId",'\N')::int as driver_id,
    nullif("points",'\N')::numeric as points,
    nullif("position",'\N')::int as standing_position,
    nullif("positionText",'\N') as position_text,
    nullif("wins",'\N')::int  as wins
from {{source('raw','driver_standings')}}