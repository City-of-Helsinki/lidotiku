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
AS SELECT lido.ecocounter_counters.id,
    lido.ecocounter_counters.name,
    lido.ecocounter_counters.classifying,
    lido.ecocounter_counters.longitude,
    lido.ecocounter_counters.latitude,
    lido.ecocounter_counters.crs_epsg,
    lido.ecocounter_counters.source,
    lido.ecocounter_counters.geom
   FROM lido.ecocounter_counters
UNION ALL
 SELECT lido.infotripla_counters.id,
    lido.infotripla_counters.name,
    lido.infotripla_counters.classifying,
    lido.infotripla_counters.longitude,
    lido.infotripla_counters.latitude,
    lido.infotripla_counters.crs_epsg,
    lido.infotripla_counters.source,
    lido.infotripla_counters.geom
   FROM lido.infotripla_counters
UNION ALL
 SELECT lido.m680_counters.id,
    lido.m680_counters.name,
    lido.m680_counters.classifying,
    lido.m680_counters.longitude,
    lido.m680_counters.latitude,
    lido.m680_counters.crs_epsg,
    lido.m680_counters.source,
    lido.m680_counters.geom
   FROM lido.m680_counters
UNION ALL
 SELECT lido.marksman_counters.id,
    lido.marksman_counters.name,
    lido.marksman_counters.classifying,
    lido.marksman_counters.longitude,
    lido.marksman_counters.latitude,
    lido.marksman_counters.crs_epsg,
    lido.marksman_counters.source,
    lido.marksman_counters.geom
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