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
AS SELECT lido.ecocounter_observations.id,
    lido.ecocounter_observations.direction,
    lido.ecocounter_observations.value,
    lido.ecocounter_observations.unit,
    lido.ecocounter_observations.typeofmeasurement,
    lido.ecocounter_observations.phenomenondurationseconds,
    lido.ecocounter_observations.vehicletype,
    lido.ecocounter_observations.datetime,
    lido.ecocounter_observations.source
   FROM lido.ecocounter_observations
UNION ALL
 SELECT lido.infotripla_observations.id,
    lido.infotripla_observations.direction,
    lido.infotripla_observations.value,
    lido.infotripla_observations.unit,
    lido.infotripla_observations.typeofmeasurement,
    lido.infotripla_observations.phenomenondurationseconds,
    lido.infotripla_observations.vehicletype,
    lido.infotripla_observations.datetime,
    lido.infotripla_observations.source
   FROM lido.infotripla_observations
UNION ALL
 SELECT lido.m680_observations.id,
    lido.m680_observations.direction,
    lido.m680_observations.value,
    lido.m680_observations.unit,
    lido.m680_observations.typeofmeasurement,
    lido.m680_observations.phenomenondurationseconds,
    lido.m680_observations.vehicletype,
    lido.m680_observations.datetime,
    lido.m680_observations.source
   FROM lido.m680_observations
UNION ALL
 SELECT lido.marksman_observations.id,
    lido.marksman_observations.direction::character varying AS direction,
    lido.marksman_observations.value,
    lido.marksman_observations.unit,
    lido.marksman_observations.typeofmeasurement,
    lido.marksman_observations.phenomenondurationseconds,
    lido.marksman_observations.vehicletype,
    lido.marksman_observations.datetime,
    lido.marksman_observations.source
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