select
    nullif("constructorStandingsId",'\N')::int as constructor_standings_id,
    nullif("raceId",'\N')::int as race_id,
    nullif("constructorId",'\N')::int as constructor_id,
    nullif("points",'\N')::numeric as points,
    nullif("position",'\N')::int as standing_position,
    nullif("positionText",'\N') as position_text,
    nullif("wins",'\N')::int  as wins
from {{source('raw','constructor_standings')}}