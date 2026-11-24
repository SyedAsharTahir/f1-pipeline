select
     driver_id,
     driver_ref,
     driver_number,
     code,
     forename,
     surname,
     date_of_birth,
     nationality,
     driver_url
from {{ref('stg_drivers')}} 
