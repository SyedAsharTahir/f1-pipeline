select
    nullif("constructorResultsId",'\N')::int as constructor_result_id,
    nullif("raceId",'\N')::int as race_id,
    nullif("constructorId",'\N')::int as constructor_id,
    nullif("points",'\N')::numeric as points,
    nullif("status",'\N') as result_status
from {{source('raw','constructor_results')}}