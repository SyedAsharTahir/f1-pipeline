select
     constructor_id,
     constructor_ref,
     constructor_name,
     nationality,
     constructor_url
from {{ref('stg_constructors')}}