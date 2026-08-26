Arrancar servicios

!140
!141
una vez dentro
starup


--select owner, table_name from sys.all_tables where table_name like 'Z_PYLOAD_VRYR%';

--select owner, table_name from sys.all_tables where table_name like 'Z_PYLOAD_RNIP_%';

-- select owner, table_name from sys.all_tables where table_name like 'Z_PYLOAD_MANDAMIENTOS%';

select count(*) from "CSNISPRNPSP"."Z_PYLOAD_RNPSP_2022_05";
DROP TABLE "CSNISPRNIP"."Z_PYLOAD_RNIP_202205";

DROP TABLE "CSNISPRNPSP"."Z_PYLOAD_RNPSP_2022_05";
'schema': "CSNISPVRYR",
        'tableName': "Z_PYLOAD_VRYR_202205",
     
DROP TABLE "CSNISPVRYR"."Z_PYLOAD_VRYR_202205";

-- select count(*) from "CSNISPRNPSP"."Z_PYLOAD_RNPSP_2021_04";
-- 4221642
-- Log: 4221642

select count(*) from "CSNISPVRYR"."Z_PYLOAD_VRYR_202408incrementaL";
-- select count(*) from "CSNISPVRYR"."Z_PYLOAD_VRYR_202408incremental";
-- 4206214
-- Log: 4206214


-- select count(*) from "CSNISPRNIP"."Z_PYLOAD_RNIP_20204";
-- 3069584 
-- Log: 3069487


-- select count(*) from "CSNISPMANDAMIENTOS"."Z_PYLOAD_MANDAMIENTOS_202104";
-- 2645533
-- Log: 2645533


-- select count(*) from "CSNISPLICENCIA"."Z_PYLOAD_LICENCIA_202104";
-- 345265
-- Log: 345265
