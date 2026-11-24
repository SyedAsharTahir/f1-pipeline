select
    nullif("driverId",'\N')::int as driver_id,
    nullif("driverRef",'\N') as driver_ref,
    nullif("number",'\N')::int as driver_number,
    nullif("code",'\N') as code,
    nullif("forename",'\N') as forename,
    nullif("surname",'\N') as surname,
    nullif("dob",'\N')::date  as date_of_birth,
    nullif("nationality",'\N')  as nationality,
    nullif("url",'\N')  as driver_url
from {{source('raw','drivers')}} 