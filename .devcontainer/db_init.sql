-- Schema
CREATE SCHEMA IF NOT EXISTS lido;


-- EcoCounter
CREATE TABLE IF NOT EXISTS lido.ecocounter_counters (
	id int8 NULL,
	"name" varchar(32) NULL,
	classifying bool NULL,
	longitude float8 NULL,
	latitude float8 NULL,
	crs_epsg int8 NULL,
	"source" varchar(32) NULL,
	geom public.geometry(geometry, 4326) NULL
);
CREATE INDEX IF NOT EXISTS ecocounter_counters_geom_1668597320638 ON lido.ecocounter_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.ecocounter_observations (
	id int8 NULL,
	direction varchar(32) NULL,
	value int8 NULL,
	unit varchar(8) NULL,
	typeofmeasurement varchar(32) NULL,
	phenomenondurationseconds int8 NULL,
	vehicletype varchar(32) NULL,
	datetime timestamp NULL,
	"source" varchar(32) NULL
);
CREATE INDEX IF NOT EXISTS ecocounter_observations_datetime_idx ON lido.ecocounter_observations USING brin (datetime) WITH (pages_per_range='64', autosummarize='on');


-- InfoTripla
CREATE TABLE IF NOT EXISTS lido.infotripla_counters (
	id int8 NULL,
	"name" varchar(32) NULL,
	classifying bool NULL,
	longitude float8 NULL,
	latitude float8 NULL,
	crs_epsg int8 NULL,
	"source" varchar(32) NULL,
	geom public.geometry(geometry, 4326) NULL
);
CREATE INDEX IF NOT EXISTS infotripla_counters_geom_1668597318594 ON lido.infotripla_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.infotripla_observations (
	id int8 NULL,
	direction varchar(32) NULL,
	value int8 NULL,
	unit varchar(8) NULL,
	typeofmeasurement varchar(32) NULL,
	phenomenondurationseconds int8 NULL,
	vehicletype varchar(32) NULL,
	datetime timestamp NULL,
	"source" varchar(32) NULL
);
CREATE INDEX IF NOT EXISTS infotripla_observations_datetime_idx ON lido.infotripla_observations USING brin (datetime) WITH (pages_per_range='64', autosummarize='on');


-- M680
CREATE TABLE IF NOT EXISTS lido.m680_counters (
	id int8 NULL,
	"name" varchar(32) NULL,
	classifying bool NULL,
	longitude float8 NULL,
	latitude float8 NULL,
	crs_epsg int8 NULL,
	"source" varchar(32) NULL,
	geom public.geometry(geometry, 4326) NULL
);
CREATE INDEX IF NOT EXISTS m680_counters_geom_1668600007799 ON lido.m680_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.m680_observations (
	id int8 NULL,
	direction varchar(32) NULL,
	value int8 NULL,
	unit varchar(8) NULL,
	typeofmeasurement varchar(32) NULL,
	phenomenondurationseconds int8 NULL,
	vehicletype varchar(32) NULL,
	datetime timestamp NULL,
	"source" varchar(32) NULL
);
CREATE INDEX IF NOT EXISTS m680_observations_datetime_idx ON lido.m680_observations USING brin (datetime) WITH (pages_per_range='64', autosummarize='on');


-- Marksman
CREATE TABLE IF NOT EXISTS lido.marksman_counters (
	id int8 NULL,
	"name" varchar(36) NULL,
	classifying bool NULL,
	longitude float8 NULL,
	latitude float8 NULL,
	crs_epsg int8 NULL,
	"source" varchar(32) NULL,
	geom public.geometry(geometry, 4326) NULL
);
CREATE INDEX IF NOT EXISTS marksman_counters_geom_1687341319448 ON lido.marksman_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.marksman_observations (
	id int8 NULL,
	direction int2 NULL,
	value int8 NULL,
	unit varchar(8) NULL,
	typeofmeasurement varchar(6) NULL,
	phenomenondurationseconds int8 NULL,
	vehicletype varchar(32) NULL,
	datetime timestamptz NULL,
	"source" varchar(9) NULL
);
CREATE INDEX IF NOT EXISTS marksman_observations_id_datetime_idx ON lido.marksman_observations USING btree (id, datetime);


-- Database views

-- lido.vw_counters source
CREATE OR REPLACE VIEW lido.vw_counters
AS SELECT DISTINCT ON (ecocounter_counters.id) ecocounter_counters.id,
    ecocounter_counters.name,
    ecocounter_counters.classifying,
    ecocounter_counters.longitude,
    ecocounter_counters.latitude,
    ecocounter_counters.crs_epsg,
    ecocounter_counters.source,
    ecocounter_counters.geom
   FROM lido.ecocounter_counters
UNION ALL
 SELECT DISTINCT ON (infotripla_counters.id) infotripla_counters.id,
    infotripla_counters.name,
    infotripla_counters.classifying,
    infotripla_counters.longitude,
    infotripla_counters.latitude,
    infotripla_counters.crs_epsg,
    infotripla_counters.source,
    infotripla_counters.geom
   FROM lido.infotripla_counters
UNION ALL
 SELECT DISTINCT ON (m680_counters.id) m680_counters.id,
    m680_counters.name,
    m680_counters.classifying,
    m680_counters.longitude,
    m680_counters.latitude,
    m680_counters.crs_epsg,
    m680_counters.source,
    m680_counters.geom
   FROM lido.m680_counters
UNION ALL
 SELECT DISTINCT ON (marksman_counters.id) marksman_counters.id,
    marksman_counters.name,
    marksman_counters.classifying,
    marksman_counters.longitude,
    marksman_counters.latitude,
    marksman_counters.crs_epsg,
    marksman_counters.source,
    marksman_counters.geom
   FROM lido.marksman_counters;


-- lido.vw_observations source
CREATE OR REPLACE VIEW lido.vw_observations
AS SELECT ecocounter_observations.id,
    ecocounter_observations.direction,
    ecocounter_observations.value,
    ecocounter_observations.unit,
    ecocounter_observations.typeofmeasurement,
    ecocounter_observations.phenomenondurationseconds,
    ecocounter_observations.vehicletype,
    ecocounter_observations.datetime::timestamp with time zone AS datetime,
    ecocounter_observations.source
   FROM lido.ecocounter_observations
UNION ALL
 SELECT infotripla_observations.id,
    infotripla_observations.direction,
    infotripla_observations.value,
    infotripla_observations.unit,
    infotripla_observations.typeofmeasurement,
    infotripla_observations.phenomenondurationseconds,
    infotripla_observations.vehicletype,
    infotripla_observations.datetime::timestamp with time zone AS datetime,
    infotripla_observations.source
   FROM lido.infotripla_observations
UNION ALL
 SELECT m680_observations.id,
    m680_observations.direction,
    m680_observations.value,
    m680_observations.unit,
    m680_observations.typeofmeasurement,
    m680_observations.phenomenondurationseconds,
    m680_observations.vehicletype,
    m680_observations.datetime::timestamp with time zone AS datetime,
    m680_observations.source
   FROM lido.m680_observations
UNION ALL
 SELECT marksman_observations.id,
    marksman_observations.direction::character varying(32) AS direction,
    marksman_observations.value,
    marksman_observations.unit,
    marksman_observations.typeofmeasurement,
    marksman_observations.phenomenondurationseconds,
    marksman_observations.vehicletype,
    marksman_observations.datetime,
    marksman_observations.source
   FROM lido.marksman_observations;


-- lido.mvw_counter_measurement_types source
-- Used to build a list of sensors from the observation data, needs to be updated
-- if new sensors/measurement types are introduces with:
-- REFRESH MATERIALIZED VIEW lido.mvw_counter_measurement_types;

CREATE MATERIALIZED VIEW lido.mvw_counter_measurement_types
TABLESPACE pg_default
AS SELECT DISTINCT ON (vw_observations.id, vw_observations.typeofmeasurement, vw_observations.phenomenondurationseconds, vw_observations.direction) vw_observations.id,
    vw_observations.typeofmeasurement,
    vw_observations.phenomenondurationseconds,
    vw_observations.direction,
    concat(
        CASE
            WHEN vw_observations.typeofmeasurement::text ~~ 'count'::text THEN 'OHITUKSET'::text
            ELSE 'KESKINOPEUS'::text
        END, '_', (vw_observations.phenomenondurationseconds / 60)::text, 'MIN', '_',
        CASE
            WHEN vw_observations.phenomenondurationseconds IS NOT NULL THEN 'KIINTEA'::text
            ELSE 'LIUKUVA'::text
        END,
        CASE
            WHEN vw_observations.direction IS NULL OR (vw_observations.direction::text = ''::text) IS TRUE THEN ''::text
            ELSE concat('_SUUNTA-', upper(replace(vw_observations.direction::text, ' '::text, '-'::text)))
        END) AS measurementtype
   FROM lido.vw_observations
WITH DATA;


-- lido.vw_counters_with_latest_sensor_observations source

CREATE OR REPLACE VIEW lido.vw_counters_with_latest_sensor_observations
AS SELECT DISTINCT ON (c.id, mt.measurementtype)
	c.id, c.name, c.source, mt.measurementtype, o.datetime, o2.value, o2.unit, o2.phenomenondurationseconds, o3.datetime AS counter_updated_at
FROM lido.vw_counters c
LEFT JOIN lido.mvw_counter_measurement_types mt ON c.id = mt.id
INNER JOIN (
	SELECT id, MAX(datetime) datetime, typeofmeasurement, phenomenondurationseconds, direction
	FROM lido.vw_observations GROUP BY id, typeofmeasurement, phenomenondurationseconds, direction
	) AS o
	ON o.id = c.id
	AND o.typeofmeasurement = mt.typeofmeasurement
	AND o.phenomenondurationseconds = mt.phenomenondurationseconds
	AND o.direction = mt.direction
INNER JOIN lido.vw_observations o2
	ON o2.datetime = o.datetime
	AND c.id = o2.id
	AND o2.typeofmeasurement = mt.typeofmeasurement
	AND o2.phenomenondurationseconds = mt.phenomenondurationseconds
	AND o2.direction = mt.direction
INNER JOIN (SELECT id, MAX(datetime) datetime FROM lido.vw_observations o3 GROUP BY id) AS o3
	ON o3.id = c.id
;