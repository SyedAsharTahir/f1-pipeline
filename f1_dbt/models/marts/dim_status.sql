select
    status_id,
    car_status
from {{ref('stg_status')}}