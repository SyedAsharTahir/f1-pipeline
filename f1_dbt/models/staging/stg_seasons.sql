select
    nullif("year",'\N')::int as season_year,
    nullif("url",'\N') as season_url
from {{source('raw','seasons')}}