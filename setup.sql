CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
CREATE EXTENSION fuzzystrmatch;
CREATE SCHEMA utils;
DROP FUNCTION utils.campos_de_tabla(character varying, character varying);

CREATE OR REPLACE FUNCTION utils.campos_de_tabla(IN sch_name character varying, IN tab_name character varying, OUT att_num smallint, OUT campo character varying, OUT tipo character varying, OUT default_value character varying, OUT uniq boolean, OUT pk boolean, OUT not_null boolean)
  RETURNS SETOF record AS
$BODY$
  select a.attnum as attnum, a.attname::varchar as campo, 
   pg_catalog.format_type(a.atttypid, a.atttypmod) as datatype, ad.adsrc as default_value,
   coalesce(pi.indisunique, false) as uniq, coalesce(pi.indisprimary, false) as pk,
   a.attnotnull as isnotnull 
  
    from pg_attribute a
      left join pg_attrdef ad
        on ad.adrelid=a.attrelid and ad.adnum=a.attnum
      inner join pg_type t
        on t.oid=a.atttypid
      left join (select indrelid, indkey[0] as indkey, max(case when indisunique=true then 1 else 0 end)::boolean as indisunique, max(case when indisprimary=true then 1 else 0 end)::boolean as indisprimary
      from pg_index 
      where array_length(indkey,1)=1
      group by indrelid, indkey[0]) pi
        on pi.indrelid=a.attrelid and pi.indisunique and a.attnum=pi.indkey
    where attrelid=(select oid
          from pg_class
          where relnamespace in (select oid from pg_namespace where nspname=$1 or (coalesce($1,'')='' and nspname=any(current_schemas(false))))
              and relname=$2
            and relkind in ('r','v'))
      and attnum>0
      and not attisdropped
      order by a.attnum;
  $BODY$
  LANGUAGE sql;
