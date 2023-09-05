-- Schema
CREATE SCHEMA IF NOT EXISTS lido;


-- EcoCounter
CREATE TABLE IF NOT EXISTS lido.ecocounter_counters (
    id bigint NOT NULL,
    name character varying(32),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326)
);
ALTER TABLE ONLY lido.ecocounter_counters
    ADD CONSTRAINT ecocounter_counters_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS ecocounter_counters_geom_1668597320638 ON lido.ecocounter_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.ecocounter_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(32) NOT NULL,
    datetime timestamp without time zone NOT NULL,
    source character varying(32)
);
ALTER TABLE ONLY lido.ecocounter_observations
    ADD CONSTRAINT ecocounter_observations_pkey PRIMARY KEY (id, typeofmeasurement, phenomenondurationseconds, vehicletype, datetime, direction);
CREATE INDEX IF NOT EXISTS ecocounter_observations_datetime_idx ON lido.ecocounter_observations USING brin (datetime) WITH (pages_per_range='64', autosummarize='on');


-- InfoTripla
CREATE TABLE IF NOT EXISTS lido.infotripla_counters (
    id bigint NOT NULL,
    name character varying(32),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326)
);
ALTER TABLE ONLY lido.infotripla_counters
    ADD CONSTRAINT infotripla_counters_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS infotripla_counters_geom_1668597318594 ON lido.infotripla_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.infotripla_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(32) NOT NULL,
    datetime timestamp without time zone NOT NULL,
    source character varying(32)
);
ALTER TABLE ONLY lido.infotripla_observations
    ADD CONSTRAINT infotripla_observations_pkey PRIMARY KEY (id, typeofmeasurement, phenomenondurationseconds, vehicletype, datetime, direction);
CREATE INDEX IF NOT EXISTS infotripla_observations_datetime_idx ON lido.infotripla_observations USING brin (datetime) WITH (pages_per_range='64', autosummarize='on');


-- M680
CREATE TABLE IF NOT EXISTS lido.m680_counters (
    id bigint NOT NULL,
    name character varying(32),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326)
);
ALTER TABLE ONLY lido.m680_counters
    ADD CONSTRAINT m680_counters_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS m680_counters_geom_1668600007799 ON lido.m680_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.m680_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(32) NOT NULL,
    datetime timestamp without time zone NOT NULL,
    source character varying(32)
);
ALTER TABLE ONLY lido.m680_observations
    ADD CONSTRAINT m680_observations_pkey PRIMARY KEY (id, typeofmeasurement, phenomenondurationseconds, vehicletype, datetime, direction);
CREATE INDEX IF NOT EXISTS m680_observations_datetime_idx ON lido.m680_observations USING brin (datetime) WITH (pages_per_range='64', autosummarize='on');


-- Marksman
CREATE TABLE IF NOT EXISTS lido.marksman_counters (
    id bigint NOT NULL,
    name character varying(36),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326)
);
ALTER TABLE ONLY lido.marksman_counters
    ADD CONSTRAINT marksman_counters_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS marksman_counters_geom_1687341319448 ON lido.marksman_counters USING gist (geom);

CREATE TABLE IF NOT EXISTS lido.marksman_observations (
    id bigint NOT NULL,
    direction smallint NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(6) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(32) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(9)
);
ALTER TABLE ONLY lido.marksman_observations
    ADD CONSTRAINT marksman_observations_pkey PRIMARY KEY (id, typeofmeasurement, phenomenondurationseconds, vehicletype, datetime, direction);
CREATE INDEX IF NOT EXISTS marksman_observations_id_datetime_idx ON lido.marksman_observations USING btree (id, datetime);


-- Creates indexes missing for the original database
CREATE INDEX IF NOT EXISTS ecocounter_observations_id_datetime_idx ON lido.ecocounter_observations USING btree (id, datetime);
CREATE INDEX IF NOT EXISTS m680_observations_id_datetime_idx ON lido.m680_observations USING btree (id, datetime);
CREATE INDEX IF NOT EXISTS infotripla_observations_id_datetime_idx ON lido.infotripla_observations USING btree (id, datetime);

-- Database views

-- lido.vw_counters source
CREATE OR REPLACE VIEW lido.vw_counters
AS SELECT ecocounter_counters.id,
    ecocounter_counters.name,
    ecocounter_counters.classifying,
    ecocounter_counters.longitude,
    ecocounter_counters.latitude,
    ecocounter_counters.crs_epsg,
    ecocounter_counters.source,
    ecocounter_counters.geom
   FROM lido.ecocounter_counters
UNION ALL
 SELECT infotripla_counters.id,
    infotripla_counters.name,
    infotripla_counters.classifying,
    infotripla_counters.longitude,
    infotripla_counters.latitude,
    infotripla_counters.crs_epsg,
    infotripla_counters.source,
    infotripla_counters.geom
   FROM lido.infotripla_counters
UNION ALL
 SELECT m680_counters.id,
    m680_counters.name,
    m680_counters.classifying,
    m680_counters.longitude,
    m680_counters.latitude,
    m680_counters.crs_epsg,
    m680_counters.source,
    m680_counters.geom
   FROM lido.m680_counters
UNION ALL
 SELECT marksman_counters.id,
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
      ecocounter_observations.source,
      ecocounter_observations.ctid
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
      infotripla_observations.source,
      infotripla_observations.ctid
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
      m680_observations.source,
      m680_observations.ctid
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
      marksman_observations.source,
      marksman_observations.ctid
   FROM lido.marksman_observations;

