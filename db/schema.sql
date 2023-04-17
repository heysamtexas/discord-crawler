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
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: channel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.channel (
    id bigint NOT NULL,
    name character varying,
    raw_data json,
    guild_id bigint NOT NULL,
    crawl_enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    last_update timestamp without time zone DEFAULT now()
);


--
-- Name: COLUMN channel.crawl_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.channel.crawl_enabled IS 'Is crawling enabled for this channel';


--
-- Name: channel_crawl_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.channel_crawl_log (
    id integer NOT NULL,
    started_at timestamp without time zone NOT NULL,
    ended_at timestamp without time zone NOT NULL,
    low_message_id bigint NOT NULL,
    high_message_id bigint,
    channel_id bigint NOT NULL
);


--
-- Name: COLUMN channel_crawl_log.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.channel_crawl_log.started_at IS 'When was the crawl completed';


--
-- Name: COLUMN channel_crawl_log.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.channel_crawl_log.ended_at IS 'When did the crawl complete';


--
-- Name: channel_crawl_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.channel_crawl_log ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.channel_crawl_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config (
    id integer NOT NULL
);


--
-- Name: config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.config ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.config_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: guild; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guild (
    id bigint NOT NULL,
    name character varying,
    raw_data json,
    selfbot_id integer,
    invite_link text,
    crawl_priority integer DEFAULT 0,
    crawl_enabled boolean DEFAULT true NOT NULL
);


--
-- Name: COLUMN guild.crawl_priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.guild.crawl_priority IS 'Give preference or penalty to specific guilds. Higher numbers go sooner than lower.';


--
-- Name: message; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.message (
    id bigint NOT NULL,
    raw_data json,
    channel_id bigint
);


--
-- Name: mv_channel_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_channel_stats AS
 SELECT g.name AS guild,
    c.name AS channel,
    count(m.id) AS message_count
   FROM ((public.channel c
     LEFT JOIN public.message m ON ((c.id = m.channel_id)))
     LEFT JOIN public.guild g ON ((g.id = c.guild_id)))
  GROUP BY c.name, g.name
  WITH NO DATA;


--
-- Name: mv_guild_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_guild_stats AS
 SELECT mv_channel_stats.guild,
    sum(mv_channel_stats.message_count) AS message_count
   FROM public.mv_channel_stats
  GROUP BY mv_channel_stats.guild
  WITH NO DATA;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: selfbot; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.selfbot (
    id integer NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    token text
);


--
-- Name: selfbot_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.selfbot ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.selfbot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: v_channel_stats; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_channel_stats AS
 SELECT g.name AS guild,
    c.name AS channel,
    count(m.id) AS message_count
   FROM ((public.channel c
     LEFT JOIN public.message m ON ((c.id = m.channel_id)))
     LEFT JOIN public.guild g ON ((g.id = c.guild_id)))
  GROUP BY c.name, g.name;


--
-- Name: VIEW v_channel_stats; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_channel_stats IS 'View rolling up some basic channel stats';


--
-- Name: v_messages; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_messages AS
 SELECT m.id,
    g.name AS guild,
    c.name AS channel,
    (m.raw_data ->> 'content'::text) AS content
   FROM ((public.message m
     LEFT JOIN public.channel c ON ((m.channel_id = c.id)))
     LEFT JOIN public.guild g ON ((c.guild_id = g.id)));


--
-- Name: channel channel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.channel
    ADD CONSTRAINT channel_pkey PRIMARY KEY (id);


--
-- Name: config config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config
    ADD CONSTRAINT config_pkey PRIMARY KEY (id);


--
-- Name: guild guild_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guild
    ADD CONSTRAINT guild_pkey PRIMARY KEY (id);


--
-- Name: message message_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: selfbot selfbot_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.selfbot
    ADD CONSTRAINT selfbot_email_key UNIQUE (email);


--
-- Name: selfbot selfbot_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.selfbot
    ADD CONSTRAINT selfbot_pkey PRIMARY KEY (id);


--
-- Name: selfbot selfbot_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.selfbot
    ADD CONSTRAINT selfbot_username_key UNIQUE (username);


--
-- Name: channel_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX channel_id_idx ON public.message USING btree (channel_id);


--
-- Name: channel channel_guild_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.channel
    ADD CONSTRAINT channel_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES public.guild(id) ON DELETE CASCADE;


--
-- Name: guild guild_selfbot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guild
    ADD CONSTRAINT guild_selfbot_id_fkey FOREIGN KEY (selfbot_id) REFERENCES public.selfbot(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20221102214739'),
    ('20221103124223');
