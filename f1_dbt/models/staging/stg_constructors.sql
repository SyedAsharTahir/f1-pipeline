select
    nullif("constructorId",'\N')::int as constructor_id,
    nullif("constructorRef",'\N') as constructor_ref,
    nullif("name",'\N') as constructor_name,
    nullif("nationality",'\N') as nationality,
    nullif("url",'\N') as constructor_url
from {{source('raw','constructors')}}