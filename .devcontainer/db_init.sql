--
-- PostgreSQL database dump
--

-- Dumped from database version 14.15 (Ubuntu 14.15-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 15.10 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: lido; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA lido;

--
-- Name: f_observations(timestamp without time zone, timestamp without time zone); Type: FUNCTION; Schema: lido; Owner: -
--

CREATE FUNCTION lido.f_observations(starttime timestamp without time zone DEFAULT '1950-01-01 00:00:00'::timestamp without time zone, endtime timestamp without time zone DEFAULT (now())::timestamp without time zone) RETURNS TABLE(id bigint, direction character varying, value bigint, unit character varying, typeofmeasurement character varying, phenomenondurationseconds bigint, vehicletype character varying, datetime timestamp with time zone, source character varying, ctid tid)
    LANGUAGE plpgsql ROWS 500000 PARALLEL SAFE
    AS $$

DECLARE

  currenttime timestamp := now()::timestamp;

BEGIN
  --Function query examples:
  --SELECT * FROM lido.f_observations('2023-08-20 16:00:00'::timestamp, '2023-08-30 18:00:00'::timestamp)
  --SELECT * FROM lido.f_observations((now() - '10day'::interval)::timestamp, now()::timestamp)

  endtime := LEAST(endtime, currenttime);


  RETURN QUERY
  SELECT ecocounter_observations.id,
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
  WHERE ecocounter_observations.datetime >= starttime
  AND   ecocounter_observations.datetime < endtime
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
  WHERE infotripla_observations.datetime >= starttime
  AND   infotripla_observations.datetime < endtime
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
  WHERE m680_observations.datetime >= starttime
  AND   m680_observations.datetime < endtime
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
  FROM lido.marksman_observations
  WHERE marksman_observations.datetime >= starttime::timestamptz
  AND   marksman_observations.datetime < endtime::timestamptz;

END;

$$;


--
-- Name: FUNCTION f_observations(starttime timestamp without time zone, endtime timestamp without time zone); Type: COMMENT; Schema: lido; Owner: -
--

COMMENT ON FUNCTION lido.f_observations(starttime timestamp without time zone, endtime timestamp without time zone) IS 'Function query examples:
SELECT * FROM lido.f_observations(''2023-08-20 16:00:00''::timestamp, ''2023-08-30 18:00:00''::timestamp)
SELECT * FROM lido.f_observations((now() - ''10day''::interval)::timestamp, now()::timestamp)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: data_sources; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.data_sources (
    name character varying(32) NOT NULL,
    description_fi character varying(1000),
    description_sv character varying(1000),
    description_en character varying(1000),
    license character varying(32)
);


--
-- Name: ecocounter_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.ecocounter_counters (
    id bigint NOT NULL,
    name character varying(50),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326),
    data_received boolean DEFAULT false,
    first_stored_observation timestamp with time zone,
    last_stored_observation timestamp with time zone,
    municipality_code smallint DEFAULT 91 NOT NULL
);


--
-- Name: ecocounter_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.ecocounter_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(32)
);


--
-- Name: liva_counter_sequence; Type: SEQUENCE; Schema: lido; Owner: -
--

CREATE SEQUENCE lido.liva_counter_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fintraffic_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.fintraffic_counters (
    id bigint DEFAULT nextval('lido.liva_counter_sequence'::regclass) NOT NULL,
    source_id bigint,
    source character varying(32) NOT NULL,
    name character varying(100) NOT NULL,
    municipality_code smallint NOT NULL,
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint DEFAULT 4326,
    geom public.geometry(Geometry,4326),
    data_received boolean,
    first_stored_observation timestamp with time zone,
    last_stored_observation timestamp with time zone
);


--
-- Name: fintraffic_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.fintraffic_observations (
    counter_id bigint NOT NULL,
    source character varying(32) NOT NULL,
    direction character varying(32) NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    typeofmeasurement character varying(32) NOT NULL,
    unit character varying(8) NOT NULL,
    value numeric(8,2)
);


--
-- Name: fintraffic_vehicle_properties; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.fintraffic_vehicle_properties (
    id smallint NOT NULL,
    code character varying(20) NOT NULL,
    description character varying(50) NOT NULL
);


--
-- Name: infotripla_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.infotripla_counters (
    id bigint NOT NULL,
    name character varying(32),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326),
    data_received boolean DEFAULT false,
    first_stored_observation timestamp with time zone,
    last_stored_observation timestamp with time zone,
    municipality_code smallint DEFAULT 91 NOT NULL
);


--
-- Name: infotripla_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.infotripla_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(32)
);


--
-- Name: liva_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.liva_counters (
    id bigint NOT NULL,
    name character varying(100),
    firsttime timestamp with time zone,
    lasttime timestamp with time zone,
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    controllerexternalcode smallint,
    detectorexternalcode character varying(8),
    omniacode smallint,
    omnianame character varying(50),
    controllerdescription character varying(100),
    data_received boolean,
    geom public.geometry(Geometry,4326),
    municipality_code smallint DEFAULT 91 NOT NULL
);


--
-- Name: liva_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.liva_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(32)
);


--
-- Name: m680_aggregates_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.m680_aggregates_counters (
    id bigint NOT NULL,
    name character varying(100),
    starttime timestamp with time zone,
    endtime timestamp with time zone,
    latitude double precision,
    longitude double precision,
    data_received boolean,
    geom public.geometry(Geometry,4326),
    classifying boolean,
    crs_epsg bigint,
    source character varying(32),
    first_stored_observation timestamp with time zone,
    last_stored_observation timestamp with time zone,
    municipality_code smallint DEFAULT 91 NOT NULL
);


--
-- Name: m680_aggregates_lane_properties; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.m680_aggregates_lane_properties (
    device_description character varying(50),
    lane_description character varying(50),
    lane_number smallint
);


--
-- Name: m680_aggregates_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.m680_aggregates_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(32),
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL
);


--
-- Name: m680_aggregates_vehicle_properties; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.m680_aggregates_vehicle_properties (
    id smallint,
    description character varying(64)
);


--
-- Name: m680_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.m680_counters (
    id bigint NOT NULL,
    name character varying(100),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326)
);


--
-- Name: m680_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.m680_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(32) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(32)
);


--
-- Name: marksman_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.marksman_counters (
    id bigint NOT NULL,
    name character varying(36),
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint,
    source character varying(32),
    geom public.geometry(Geometry,4326),
    source_id bigint,
    data_received boolean DEFAULT false,
    first_stored_observation timestamp with time zone,
    last_stored_observation timestamp with time zone,
    municipality_code smallint DEFAULT 91 NOT NULL
);


--
-- Name: marksman_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.marksman_observations (
    id bigint NOT NULL,
    direction character varying(32) NOT NULL,
    value bigint,
    unit character varying(8),
    typeofmeasurement character varying(6) NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    source character varying(9)
);


--
-- Name: smartjunction_counters; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.smartjunction_counters (
    id bigint DEFAULT nextval('lido.liva_counter_sequence'::regclass) NOT NULL,
    source_id bigint,
    source character varying(32) NOT NULL,
    name character varying(100) NOT NULL,
    municipality_code smallint NOT NULL,
    classifying boolean,
    longitude double precision,
    latitude double precision,
    crs_epsg bigint DEFAULT 4326,
    geom public.geometry(Geometry,4326),
    data_received boolean,
    first_stored_observation timestamp with time zone,
    last_stored_observation timestamp with time zone
);


--
-- Name: smartjunction_observations; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.smartjunction_observations (
    counter_id bigint NOT NULL,
    source character varying(32) NOT NULL,
    direction character varying(32) NOT NULL,
    vehicletype character varying(50) NOT NULL,
    datetime timestamp with time zone NOT NULL,
    phenomenondurationseconds bigint NOT NULL,
    typeofmeasurement character varying(32) NOT NULL,
    unit character varying(8) NOT NULL,
    value numeric(8,2)
);


--
-- Name: smartjunction_vehicle_properties; Type: TABLE; Schema: lido; Owner: -
--

CREATE TABLE lido.smartjunction_vehicle_properties (
    code character varying(20) NOT NULL,
    description character varying(50) NOT NULL
);


--
-- Name: vw_counters; Type: VIEW; Schema: lido; Owner: -
--

CREATE VIEW lido.vw_counters AS
 SELECT ecocounter_counters.id,
    (ecocounter_counters.name)::character varying(100) AS name,
    ecocounter_counters.classifying,
    ecocounter_counters.longitude,
    ecocounter_counters.latitude,
    ecocounter_counters.crs_epsg,
    ecocounter_counters.source,
    ecocounter_counters.geom,
    ecocounter_counters.municipality_code,
    ecocounter_counters.data_received,
    ecocounter_counters.first_stored_observation,
    ecocounter_counters.last_stored_observation,
    ecocounter_counters.id AS source_id
   FROM lido.ecocounter_counters
UNION ALL
 SELECT infotripla_counters.id,
    (
        CASE
            WHEN ((COALESCE(infotripla_counters.name, ''::character varying))::text <> ''::text) THEN infotripla_counters.name
            ELSE infotripla_counters.source
        END)::character varying(100) AS name,
    infotripla_counters.classifying,
    infotripla_counters.longitude,
    infotripla_counters.latitude,
    infotripla_counters.crs_epsg,
    'InfoTripla'::character varying(32) AS source,
    infotripla_counters.geom,
    infotripla_counters.municipality_code,
    infotripla_counters.data_received,
    infotripla_counters.first_stored_observation,
    infotripla_counters.last_stored_observation,
    infotripla_counters.id AS source_id
   FROM lido.infotripla_counters
UNION ALL
 SELECT m680_aggregates_counters.id,
    m680_aggregates_counters.name,
    m680_aggregates_counters.classifying,
    m680_aggregates_counters.longitude,
    m680_aggregates_counters.latitude,
    m680_aggregates_counters.crs_epsg,
    m680_aggregates_counters.source,
    m680_aggregates_counters.geom,
    m680_aggregates_counters.municipality_code,
    m680_aggregates_counters.data_received,
    m680_aggregates_counters.first_stored_observation,
    m680_aggregates_counters.last_stored_observation,
    m680_aggregates_counters.id AS source_id
   FROM lido.m680_aggregates_counters
UNION ALL
 SELECT marksman_counters.id,
    (marksman_counters.name)::character varying(100) AS name,
    marksman_counters.classifying,
    marksman_counters.longitude,
    marksman_counters.latitude,
    marksman_counters.crs_epsg,
    marksman_counters.source,
    marksman_counters.geom,
    marksman_counters.municipality_code,
    marksman_counters.data_received,
    marksman_counters.first_stored_observation,
    marksman_counters.last_stored_observation,
    marksman_counters.source_id
   FROM lido.marksman_counters
UNION ALL
 SELECT liva_counters.id,
    liva_counters.name,
    liva_counters.classifying,
    liva_counters.longitude,
    liva_counters.latitude,
    liva_counters.crs_epsg,
    liva_counters.source,
    (public.st_centroid(liva_counters.geom))::public.geometry(Geometry,4326) AS geom,
    liva_counters.municipality_code,
    liva_counters.data_received,
    liva_counters.firsttime AS first_stored_observation,
    liva_counters.lasttime AS last_stored_observation,
    NULL::bigint AS source_id
   FROM lido.liva_counters
UNION ALL
 SELECT fintraffic_counters.id,
    fintraffic_counters.name,
    fintraffic_counters.classifying,
    fintraffic_counters.longitude,
    fintraffic_counters.latitude,
    fintraffic_counters.crs_epsg,
    fintraffic_counters.source,
    (public.st_centroid(fintraffic_counters.geom))::public.geometry(Geometry,4326) AS geom,
    fintraffic_counters.municipality_code,
    fintraffic_counters.data_received,
    fintraffic_counters.first_stored_observation,
    fintraffic_counters.last_stored_observation,
    fintraffic_counters.source_id
   FROM lido.fintraffic_counters
UNION ALL
 SELECT smartjunction_counters.id,
    smartjunction_counters.name,
    smartjunction_counters.classifying,
    smartjunction_counters.longitude,
    smartjunction_counters.latitude,
    smartjunction_counters.crs_epsg,
    smartjunction_counters.source,
    (public.st_centroid(smartjunction_counters.geom))::public.geometry(Geometry,4326) AS geom,
    smartjunction_counters.municipality_code,
    smartjunction_counters.data_received,
    smartjunction_counters.first_stored_observation,
    smartjunction_counters.last_stored_observation,
    smartjunction_counters.source_id
   FROM lido.smartjunction_counters;


--
-- Name: vw_counters_bup; Type: VIEW; Schema: lido; Owner: -
--

CREATE VIEW lido.vw_counters_bup AS
 SELECT ecocounter_counters.id,
    (ecocounter_counters.name)::character varying(100) AS name,
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
 SELECT m680_aggregates_counters.id,
    m680_aggregates_counters.name,
    m680_aggregates_counters.classifying,
    m680_aggregates_counters.longitude,
    m680_aggregates_counters.latitude,
    m680_aggregates_counters.crs_epsg,
    m680_aggregates_counters.source,
    m680_aggregates_counters.geom
   FROM lido.m680_aggregates_counters
UNION ALL
 SELECT marksman_counters.id,
    marksman_counters.name,
    marksman_counters.classifying,
    marksman_counters.longitude,
    marksman_counters.latitude,
    marksman_counters.crs_epsg,
    marksman_counters.source,
    marksman_counters.geom
   FROM lido.marksman_counters
UNION ALL
 SELECT liva_counters.id,
    liva_counters.name,
    liva_counters.classifying,
    liva_counters.longitude,
    liva_counters.latitude,
    liva_counters.crs_epsg,
    liva_counters.source,
    (public.st_centroid(liva_counters.geom))::public.geometry(Geometry,4326) AS geom
   FROM lido.liva_counters;


--
-- Name: vw_observations; Type: VIEW; Schema: lido; Owner: -
--

CREATE VIEW lido.vw_observations AS
 SELECT ecocounter_observations.id,
    ecocounter_observations.direction,
    ecocounter_observations.value,
    ecocounter_observations.unit,
    ecocounter_observations.typeofmeasurement,
    ecocounter_observations.phenomenondurationseconds,
    ecocounter_observations.vehicletype,
    ecocounter_observations.datetime,
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
    infotripla_observations.datetime,
    infotripla_observations.source,
    infotripla_observations.ctid
   FROM lido.infotripla_observations
UNION ALL
 SELECT m680_aggregates_observations.id,
    m680_aggregates_observations.direction,
    m680_aggregates_observations.value,
    m680_aggregates_observations.unit,
    m680_aggregates_observations.typeofmeasurement,
    m680_aggregates_observations.phenomenondurationseconds,
    m680_aggregates_observations.vehicletype,
    m680_aggregates_observations.datetime,
    m680_aggregates_observations.source,
    m680_aggregates_observations.ctid
   FROM lido.m680_aggregates_observations
UNION ALL
 SELECT marksman_observations.id,
    marksman_observations.direction,
    marksman_observations.value,
    marksman_observations.unit,
    (marksman_observations.typeofmeasurement)::character varying(32) AS typeofmeasurement,
    marksman_observations.phenomenondurationseconds,
    marksman_observations.vehicletype,
    marksman_observations.datetime,
    (marksman_observations.source)::character varying(32) AS source,
    marksman_observations.ctid
   FROM lido.marksman_observations
UNION ALL
 SELECT liva_observations.id,
    liva_observations.direction,
    liva_observations.value,
    liva_observations.unit,
    liva_observations.typeofmeasurement,
    liva_observations.phenomenondurationseconds,
    liva_observations.vehicletype,
    liva_observations.datetime,
    liva_observations.source,
    liva_observations.ctid
   FROM lido.liva_observations
UNION ALL
 SELECT fintraffic_observations.counter_id AS id,
    fintraffic_observations.direction,
    (fintraffic_observations.value)::integer AS value,
    fintraffic_observations.unit,
    fintraffic_observations.typeofmeasurement,
    fintraffic_observations.phenomenondurationseconds,
    fintraffic_observations.vehicletype,
    fintraffic_observations.datetime,
    fintraffic_observations.source,
    fintraffic_observations.ctid
   FROM lido.fintraffic_observations
UNION ALL
 SELECT smartjunction_observations.counter_id AS id,
    smartjunction_observations.direction,
    (smartjunction_observations.value)::integer AS value,
    smartjunction_observations.unit,
    smartjunction_observations.typeofmeasurement,
    smartjunction_observations.phenomenondurationseconds,
    smartjunction_observations.vehicletype,
    smartjunction_observations.datetime,
    smartjunction_observations.source,
    smartjunction_observations.ctid
   FROM lido.smartjunction_observations;


--
-- Name: vw_observations_bup; Type: VIEW; Schema: lido; Owner: -
--

CREATE VIEW lido.vw_observations_bup AS
 SELECT ecocounter_observations.id,
    ecocounter_observations.direction,
    ecocounter_observations.value,
    ecocounter_observations.unit,
    ecocounter_observations.typeofmeasurement,
    ecocounter_observations.phenomenondurationseconds,
    ecocounter_observations.vehicletype,
    ecocounter_observations.datetime,
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
    infotripla_observations.datetime,
    infotripla_observations.source,
    infotripla_observations.ctid
   FROM lido.infotripla_observations
UNION ALL
 SELECT m680_aggregates_observations.id,
    m680_aggregates_observations.direction,
    m680_aggregates_observations.value,
    m680_aggregates_observations.unit,
    m680_aggregates_observations.typeofmeasurement,
    m680_aggregates_observations.phenomenondurationseconds,
    m680_aggregates_observations.vehicletype,
    m680_aggregates_observations.datetime,
    m680_aggregates_observations.source,
    m680_aggregates_observations.ctid
   FROM lido.m680_aggregates_observations
UNION ALL
 SELECT marksman_observations.id,
    marksman_observations.direction,
    marksman_observations.value,
    marksman_observations.unit,
    marksman_observations.typeofmeasurement,
    marksman_observations.phenomenondurationseconds,
    marksman_observations.vehicletype,
    marksman_observations.datetime,
    marksman_observations.source,
    marksman_observations.ctid
   FROM lido.marksman_observations
UNION ALL
 SELECT liva_observations.id,
    liva_observations.direction,
    liva_observations.value,
    liva_observations.unit,
    liva_observations.typeofmeasurement,
    liva_observations.phenomenondurationseconds,
    liva_observations.vehicletype,
    liva_observations.datetime,
    liva_observations.source,
    liva_observations.ctid
   FROM lido.liva_observations;


--
-- Name: vw_observations_by_time_interval; Type: VIEW; Schema: lido; Owner: -
--

CREATE VIEW lido.vw_observations_by_time_interval AS
 SELECT ecocounter_observations.id,
    ecocounter_observations.direction,
    ecocounter_observations.value,
    ecocounter_observations.unit,
    ecocounter_observations.typeofmeasurement,
    ecocounter_observations.phenomenondurationseconds,
    ecocounter_observations.vehicletype,
    ecocounter_observations.datetime,
    ecocounter_observations.source,
    ecocounter_observations.ctid
   FROM lido.ecocounter_observations
  WHERE ((ecocounter_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp without time zone) AND (ecocounter_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp without time zone))
UNION ALL
 SELECT infotripla_observations.id,
    infotripla_observations.direction,
    infotripla_observations.value,
    infotripla_observations.unit,
    infotripla_observations.typeofmeasurement,
    infotripla_observations.phenomenondurationseconds,
    infotripla_observations.vehicletype,
    infotripla_observations.datetime,
    infotripla_observations.source,
    infotripla_observations.ctid
   FROM lido.infotripla_observations
  WHERE ((infotripla_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp without time zone) AND (infotripla_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp without time zone))
UNION ALL
 SELECT m680_aggregates_observations.id,
    m680_aggregates_observations.direction,
    m680_aggregates_observations.value,
    m680_aggregates_observations.unit,
    m680_aggregates_observations.typeofmeasurement,
    m680_aggregates_observations.phenomenondurationseconds,
    m680_aggregates_observations.vehicletype,
    m680_aggregates_observations.datetime,
    m680_aggregates_observations.source,
    m680_aggregates_observations.ctid
   FROM lido.m680_aggregates_observations
  WHERE ((m680_aggregates_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp without time zone) AND (m680_aggregates_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp without time zone))
UNION ALL
 SELECT marksman_observations.id,
    marksman_observations.direction,
    marksman_observations.value,
    marksman_observations.unit,
    (marksman_observations.typeofmeasurement)::character varying(32) AS typeofmeasurement,
    marksman_observations.phenomenondurationseconds,
    marksman_observations.vehicletype,
    marksman_observations.datetime,
    (marksman_observations.source)::character varying(32) AS source,
    marksman_observations.ctid
   FROM lido.marksman_observations
  WHERE ((marksman_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp with time zone) AND (marksman_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp with time zone))
UNION ALL
 SELECT liva_observations.id,
    liva_observations.direction,
    liva_observations.value,
    liva_observations.unit,
    liva_observations.typeofmeasurement,
    liva_observations.phenomenondurationseconds,
    liva_observations.vehicletype,
    liva_observations.datetime,
    liva_observations.source,
    liva_observations.ctid
   FROM lido.liva_observations
  WHERE ((liva_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp with time zone) AND (liva_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp with time zone))
UNION ALL
 SELECT fintraffic_observations.counter_id AS id,
    fintraffic_observations.direction,
    (fintraffic_observations.value)::integer AS value,
    fintraffic_observations.unit,
    fintraffic_observations.typeofmeasurement,
    fintraffic_observations.phenomenondurationseconds,
    fintraffic_observations.vehicletype,
    fintraffic_observations.datetime,
    fintraffic_observations.source,
    fintraffic_observations.ctid
   FROM lido.fintraffic_observations
  WHERE ((fintraffic_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp with time zone) AND (fintraffic_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp with time zone))
UNION ALL
 SELECT smartjunction_observations.counter_id AS id,
    smartjunction_observations.direction,
    (smartjunction_observations.value)::integer AS value,
    smartjunction_observations.unit,
    smartjunction_observations.typeofmeasurement,
    smartjunction_observations.phenomenondurationseconds,
    smartjunction_observations.vehicletype,
    smartjunction_observations.datetime,
    smartjunction_observations.source,
    smartjunction_observations.ctid
   FROM lido.smartjunction_observations
  WHERE ((smartjunction_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp with time zone) AND (smartjunction_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp with time zone));


--
-- Name: vw_observations_by_time_interval_bup; Type: VIEW; Schema: lido; Owner: -
--

CREATE VIEW lido.vw_observations_by_time_interval_bup AS
 SELECT ecocounter_observations.id,
    ecocounter_observations.direction,
    ecocounter_observations.value,
    ecocounter_observations.unit,
    ecocounter_observations.typeofmeasurement,
    ecocounter_observations.phenomenondurationseconds,
    ecocounter_observations.vehicletype,
    ecocounter_observations.datetime,
    ecocounter_observations.source,
    ecocounter_observations.ctid
   FROM lido.ecocounter_observations
  WHERE ((ecocounter_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp without time zone) AND (ecocounter_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp without time zone))
UNION ALL
 SELECT infotripla_observations.id,
    infotripla_observations.direction,
    infotripla_observations.value,
    infotripla_observations.unit,
    infotripla_observations.typeofmeasurement,
    infotripla_observations.phenomenondurationseconds,
    infotripla_observations.vehicletype,
    infotripla_observations.datetime,
    infotripla_observations.source,
    infotripla_observations.ctid
   FROM lido.infotripla_observations
  WHERE ((infotripla_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp without time zone) AND (infotripla_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp without time zone))
UNION ALL
 SELECT m680_aggregates_observations.id,
    m680_aggregates_observations.direction,
    m680_aggregates_observations.value,
    m680_aggregates_observations.unit,
    m680_aggregates_observations.typeofmeasurement,
    m680_aggregates_observations.phenomenondurationseconds,
    m680_aggregates_observations.vehicletype,
    m680_aggregates_observations.datetime,
    m680_aggregates_observations.source,
    m680_aggregates_observations.ctid
   FROM lido.m680_aggregates_observations
  WHERE ((m680_aggregates_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp without time zone) AND (m680_aggregates_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp without time zone))
UNION ALL
 SELECT marksman_observations.id,
    marksman_observations.direction,
    marksman_observations.value,
    marksman_observations.unit,
    marksman_observations.typeofmeasurement,
    marksman_observations.phenomenondurationseconds,
    marksman_observations.vehicletype,
    marksman_observations.datetime,
    marksman_observations.source,
    marksman_observations.ctid
   FROM lido.marksman_observations
  WHERE ((marksman_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp with time zone) AND (marksman_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp with time zone))
UNION ALL
 SELECT liva_observations.id,
    liva_observations.direction,
    liva_observations.value,
    liva_observations.unit,
    liva_observations.typeofmeasurement,
    liva_observations.phenomenondurationseconds,
    liva_observations.vehicletype,
    liva_observations.datetime,
    liva_observations.source,
    liva_observations.ctid
   FROM lido.liva_observations
  WHERE ((liva_observations.datetime >= (current_setting('lido_sessionparameter.starttime'::text))::timestamp with time zone) AND (liva_observations.datetime < (current_setting('lido_sessionparameter.endtime'::text))::timestamp with time zone));


--
-- Name: data_sources data_sources_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.data_sources
    ADD CONSTRAINT data_sources_pkey PRIMARY KEY (name);


--
-- Name: m680_aggregates_counters devices_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.m680_aggregates_counters
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: ecocounter_counters ecocounter_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.ecocounter_counters
    ADD CONSTRAINT ecocounter_counters_pkey PRIMARY KEY (id);


--
-- Name: ecocounter_observations ecocounter_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.ecocounter_observations
    ADD CONSTRAINT ecocounter_observations_pkey PRIMARY KEY (id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: fintraffic_counters fintraffic_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.fintraffic_counters
    ADD CONSTRAINT fintraffic_counters_pkey PRIMARY KEY (id);


--
-- Name: fintraffic_observations fintraffic_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.fintraffic_observations
    ADD CONSTRAINT fintraffic_observations_pkey PRIMARY KEY (counter_id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: fintraffic_vehicle_properties fintraffic_vehicle_properties_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.fintraffic_vehicle_properties
    ADD CONSTRAINT fintraffic_vehicle_properties_pkey PRIMARY KEY (id);


--
-- Name: infotripla_counters infotripla_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.infotripla_counters
    ADD CONSTRAINT infotripla_counters_pkey PRIMARY KEY (id);


--
-- Name: infotripla_observations infotripla_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.infotripla_observations
    ADD CONSTRAINT infotripla_observations_pkey PRIMARY KEY (id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: liva_counters liva_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.liva_counters
    ADD CONSTRAINT liva_counters_pkey PRIMARY KEY (id);


--
-- Name: liva_observations liva_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.liva_observations
    ADD CONSTRAINT liva_observations_pkey PRIMARY KEY (id, datetime, phenomenondurationseconds);


--
-- Name: m680_counters m680_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.m680_counters
    ADD CONSTRAINT m680_counters_pkey PRIMARY KEY (id);


--
-- Name: m680_observations m680_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.m680_observations
    ADD CONSTRAINT m680_observations_pkey PRIMARY KEY (id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: marksman_counters marksman_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.marksman_counters
    ADD CONSTRAINT marksman_counters_pkey PRIMARY KEY (id);


--
-- Name: marksman_observations marksman_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.marksman_observations
    ADD CONSTRAINT marksman_observations_pkey PRIMARY KEY (id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: m680_aggregates_observations nodeon_aggregates_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.m680_aggregates_observations
    ADD CONSTRAINT nodeon_aggregates_pkey PRIMARY KEY (id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: smartjunction_counters smartjunction_counters_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.smartjunction_counters
    ADD CONSTRAINT smartjunction_counters_pkey PRIMARY KEY (id);


--
-- Name: smartjunction_observations smartjunction_observations_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.smartjunction_observations
    ADD CONSTRAINT smartjunction_observations_pkey PRIMARY KEY (counter_id, typeofmeasurement, datetime, phenomenondurationseconds, vehicletype, direction);


--
-- Name: smartjunction_vehicle_properties smartjunction_vehicle_properties_pkey; Type: CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.smartjunction_vehicle_properties
    ADD CONSTRAINT smartjunction_vehicle_properties_pkey PRIMARY KEY (code);


--
-- Name: devices_geom; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX devices_geom ON lido.m680_aggregates_counters USING gist (geom);


--
-- Name: ecocounter_counters_geom_1668597320638; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX ecocounter_counters_geom_1668597320638 ON lido.ecocounter_counters USING gist (geom);


--
-- Name: ecocounter_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX ecocounter_observations_datetime_pkey_idx ON lido.ecocounter_observations USING btree (datetime, id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: fintraffic_counters_geom_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX fintraffic_counters_geom_idx ON lido.fintraffic_counters USING gist (geom);


--
-- Name: fintraffic_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX fintraffic_observations_datetime_pkey_idx ON lido.fintraffic_observations USING btree (datetime, counter_id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: infotripla_counters_geom_1668597318594; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX infotripla_counters_geom_1668597318594 ON lido.infotripla_counters USING gist (geom);


--
-- Name: infotripla_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX infotripla_observations_datetime_pkey_idx ON lido.infotripla_observations USING btree (datetime, id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: liva_counters_geom_1668597320638; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX liva_counters_geom_1668597320638 ON lido.liva_counters USING gist (geom);


--
-- Name: liva_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX liva_observations_datetime_pkey_idx ON lido.liva_observations USING btree (datetime, id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: m680_aggregates_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX m680_aggregates_observations_datetime_pkey_idx ON lido.m680_aggregates_observations USING btree (datetime, id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: m680_counters_geom_1668600007799; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX m680_counters_geom_1668600007799 ON lido.m680_counters USING gist (geom);


--
-- Name: m680_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX m680_observations_datetime_pkey_idx ON lido.m680_observations USING btree (datetime, id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: marksman_counters_geom_1687341319448; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX marksman_counters_geom_1687341319448 ON lido.marksman_counters USING gist (geom);


--
-- Name: marksman_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX marksman_observations_datetime_pkey_idx ON lido.marksman_observations USING btree (datetime, id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: smartjunction_counters_geom_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE INDEX smartjunction_counters_geom_idx ON lido.smartjunction_counters USING gist (geom);


--
-- Name: smartjunction_observations_datetime_pkey_idx; Type: INDEX; Schema: lido; Owner: -
--

CREATE UNIQUE INDEX smartjunction_observations_datetime_pkey_idx ON lido.smartjunction_observations USING btree (datetime, counter_id, typeofmeasurement, phenomenondurationseconds, vehicletype, direction);


--
-- Name: fintraffic_counters fintraffic_counters_source_fkey; Type: FK CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.fintraffic_counters
    ADD CONSTRAINT fintraffic_counters_source_fkey FOREIGN KEY (source) REFERENCES lido.data_sources(name);


--
-- Name: fintraffic_observations fintraffic_observations_counter_fkey; Type: FK CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.fintraffic_observations
    ADD CONSTRAINT fintraffic_observations_counter_fkey FOREIGN KEY (counter_id) REFERENCES lido.fintraffic_counters(id);


--
-- Name: fintraffic_observations fintraffic_observations_source_fkey; Type: FK CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.fintraffic_observations
    ADD CONSTRAINT fintraffic_observations_source_fkey FOREIGN KEY (source) REFERENCES lido.data_sources(name);


--
-- Name: smartjunction_counters smartjunction_counters_source_fkey; Type: FK CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.smartjunction_counters
    ADD CONSTRAINT smartjunction_counters_source_fkey FOREIGN KEY (source) REFERENCES lido.data_sources(name);


--
-- Name: smartjunction_observations smartjunction_observations_counter_fkey; Type: FK CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.smartjunction_observations
    ADD CONSTRAINT smartjunction_observations_counter_fkey FOREIGN KEY (counter_id) REFERENCES lido.smartjunction_counters(id);


--
-- Name: smartjunction_observations smartjunction_observations_source_fkey; Type: FK CONSTRAINT; Schema: lido; Owner: -
--

ALTER TABLE ONLY lido.smartjunction_observations
    ADD CONSTRAINT smartjunction_observations_source_fkey FOREIGN KEY (source) REFERENCES lido.data_sources(name);


--
-- PostgreSQL database dump complete
--

