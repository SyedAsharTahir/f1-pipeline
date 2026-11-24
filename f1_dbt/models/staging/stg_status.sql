select
    nullif("statusId",'\N')::int as status_id,
    nullif("status",'\N') as car_status
from {{source('raw','status')}}