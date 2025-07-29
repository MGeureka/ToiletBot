--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: accounts; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA accounts;


ALTER SCHEMA accounts OWNER TO mg;

--
-- Name: guilds; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA guilds;


ALTER SCHEMA guilds OWNER TO mg;

--
-- Name: leaderboards; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA leaderboards;


ALTER SCHEMA leaderboards OWNER TO mg;

--
-- Name: profiles; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA profiles;


ALTER SCHEMA profiles OWNER TO mg;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: global_aimlabs_accounts; Type: TABLE; Schema: accounts; Owner: postgres
--

CREATE TABLE accounts.global_aimlabs_accounts (
    aimlabs_id text NOT NULL,
    aimlabs_username text NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone,
    is_tracked boolean
);


ALTER TABLE accounts.global_aimlabs_accounts OWNER TO mg;

--
-- Name: global_kovaaks_accounts; Type: TABLE; Schema: accounts; Owner: postgres
--

CREATE TABLE accounts.global_kovaaks_accounts (
    kovaaks_id text NOT NULL,
    kovaaks_username text NOT NULL,
    steam_id text NOT NULL,
    steam_username text NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone,
    is_tracked boolean
);


ALTER TABLE accounts.global_kovaaks_accounts OWNER TO mg;

--
-- Name: global_valorant_accounts; Type: TABLE; Schema: accounts; Owner: postgres
--

CREATE TABLE accounts.global_valorant_accounts (
    valorant_id text NOT NULL,
    valorant_username text NOT NULL,
    valorant_tag text NOT NULL,
    region text NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone,
    is_tracked boolean
);


ALTER TABLE accounts.global_valorant_accounts OWNER TO mg;

--
-- Name: guild_leaderboard_settings; Type: TABLE; Schema: guilds; Owner: postgres
--

CREATE TABLE guilds.guild_leaderboard_settings (
    guild_id bigint NOT NULL,
    leaderboard_type text NOT NULL,
    is_enabled boolean NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE guilds.guild_leaderboard_settings OWNER TO mg;

--
-- Name: guild_membership; Type: TABLE; Schema: guilds; Owner: postgres
--

CREATE TABLE guilds.guild_membership (
    guild_id bigint NOT NULL,
    discord_id bigint NOT NULL,
    date_added timestamp with time zone NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE guilds.guild_membership OWNER TO mg;

--
-- Name: guild_settings; Type: TABLE; Schema: guilds; Owner: postgres
--

CREATE TABLE guilds.guild_settings (
    guild_id bigint NOT NULL,
    leaderboard_channel_id bigint,
    leaderboard_message_id bigint,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE guilds.guild_settings OWNER TO mg;

--
-- Name: guilds; Type: TABLE; Schema: guilds; Owner: postgres
--

CREATE TABLE guilds.guilds (
    guild_id bigint NOT NULL,
    guild_name text NOT NULL,
    added_date timestamp with time zone NOT NULL,
    last_updated timestamp with time zone NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE guilds.guilds OWNER TO mg;

--
-- Name: dojo_advanced_playlist; Type: TABLE; Schema: leaderboards; Owner: postgres
--

CREATE TABLE leaderboards.dojo_advanced_playlist (
    profile_id integer NOT NULL,
    score integer NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE leaderboards.dojo_advanced_playlist OWNER TO mg;

--
-- Name: dojo_balanced_playlist; Type: TABLE; Schema: leaderboards; Owner: postgres
--

CREATE TABLE leaderboards.dojo_balanced_playlist (
    profile_id integer NOT NULL,
    score integer NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE leaderboards.dojo_balanced_playlist OWNER TO mg;

--
-- Name: valorant_dm; Type: TABLE; Schema: leaderboards; Owner: postgres
--

CREATE TABLE leaderboards.valorant_dm (
    profile_id integer NOT NULL,
    dm jsonb NOT NULL,
    dm_count integer NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE leaderboards.valorant_dm OWNER TO mg;

--
-- Name: valorant_rank; Type: TABLE; Schema: leaderboards; Owner: postgres
--

CREATE TABLE leaderboards.valorant_rank (
    profile_id integer NOT NULL,
    current_rank text NOT NULL,
    current_rank_id text NOT NULL,
    peak_rank text NOT NULL,
    peak_rank_id text NOT NULL,
    current_rr text NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE leaderboards.valorant_rank OWNER TO mg;

--
-- Name: voltaic_s5; Type: TABLE; Schema: leaderboards; Owner: postgres
--

CREATE TABLE leaderboards.voltaic_s5 (
    profile_id integer NOT NULL,
    rank text NOT NULL,
    rank_id text NOT NULL,
    rank_rating text NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE leaderboards.voltaic_s5 OWNER TO mg;

--
-- Name: voltaic_val_s1; Type: TABLE; Schema: leaderboards; Owner: postgres
--

CREATE TABLE leaderboards.voltaic_val_s1 (
    profile_id integer NOT NULL,
    rank text NOT NULL,
    rank_id text NOT NULL,
    rank_rating text NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE leaderboards.voltaic_val_s1 OWNER TO mg;

--
-- Name: aimlabs_profiles; Type: TABLE; Schema: profiles; Owner: postgres
--

CREATE TABLE profiles.aimlabs_profiles (
    profile_id integer NOT NULL,
    discord_id bigint NOT NULL,
    aimlabs_id text NOT NULL,
    guild_id bigint NOT NULL,
    is_active boolean NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE profiles.aimlabs_profiles OWNER TO mg;

--
-- Name: aimlabs_profiles_profile_id_seq; Type: SEQUENCE; Schema: profiles; Owner: postgres
--

CREATE SEQUENCE profiles.aimlabs_profiles_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE profiles.aimlabs_profiles_profile_id_seq OWNER TO mg;

--
-- Name: aimlabs_profiles_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: postgres
--

ALTER SEQUENCE profiles.aimlabs_profiles_profile_id_seq OWNED BY profiles.aimlabs_profiles.profile_id;


--
-- Name: discord_profiles; Type: TABLE; Schema: profiles; Owner: postgres
--

CREATE TABLE profiles.discord_profiles (
    discord_id bigint NOT NULL,
    discord_username text NOT NULL,
    discord_avatar_key text NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE profiles.discord_profiles OWNER TO mg;

--
-- Name: kovaaks_profiles; Type: TABLE; Schema: profiles; Owner: postgres
--

CREATE TABLE profiles.kovaaks_profiles (
    profile_id integer NOT NULL,
    discord_id bigint NOT NULL,
    guild_id bigint NOT NULL,
    kovaaks_id text NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE profiles.kovaaks_profiles OWNER TO mg;

--
-- Name: kovaaks_profiles_profile_id_seq; Type: SEQUENCE; Schema: profiles; Owner: postgres
--

CREATE SEQUENCE profiles.kovaaks_profiles_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE profiles.kovaaks_profiles_profile_id_seq OWNER TO mg;

--
-- Name: kovaaks_profiles_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: postgres
--

ALTER SEQUENCE profiles.kovaaks_profiles_profile_id_seq OWNED BY profiles.kovaaks_profiles.profile_id;


--
-- Name: valorant_profiles; Type: TABLE; Schema: profiles; Owner: postgres
--

CREATE TABLE profiles.valorant_profiles (
    profile_id integer NOT NULL,
    discord_id bigint NOT NULL,
    guild_id bigint NOT NULL,
    valorant_id text NOT NULL,
    is_active boolean NOT NULL,
    date_added timestamp with time zone NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


ALTER TABLE profiles.valorant_profiles OWNER TO mg;

--
-- Name: valorant_profiles_profile_id_seq; Type: SEQUENCE; Schema: profiles; Owner: postgres
--

CREATE SEQUENCE profiles.valorant_profiles_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE profiles.valorant_profiles_profile_id_seq OWNER TO mg;

--
-- Name: valorant_profiles_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: postgres
--

ALTER SEQUENCE profiles.valorant_profiles_profile_id_seq OWNED BY profiles.valorant_profiles.profile_id;


--
-- Name: aimlabs_profiles profile_id; Type: DEFAULT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.aimlabs_profiles ALTER COLUMN profile_id SET DEFAULT nextval('profiles.aimlabs_profiles_profile_id_seq'::regclass);


--
-- Name: kovaaks_profiles profile_id; Type: DEFAULT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.kovaaks_profiles ALTER COLUMN profile_id SET DEFAULT nextval('profiles.kovaaks_profiles_profile_id_seq'::regclass);


--
-- Name: valorant_profiles profile_id; Type: DEFAULT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.valorant_profiles ALTER COLUMN profile_id SET DEFAULT nextval('profiles.valorant_profiles_profile_id_seq'::regclass);


--
-- Name: global_aimlabs_accounts global_aimlabs_accounts_pkey; Type: CONSTRAINT; Schema: accounts; Owner: postgres
--

ALTER TABLE ONLY accounts.global_aimlabs_accounts
    ADD CONSTRAINT global_aimlabs_accounts_pkey PRIMARY KEY (aimlabs_id);


--
-- Name: global_kovaaks_accounts global_kovaaks_accounts_pkey; Type: CONSTRAINT; Schema: accounts; Owner: postgres
--

ALTER TABLE ONLY accounts.global_kovaaks_accounts
    ADD CONSTRAINT global_kovaaks_accounts_pkey PRIMARY KEY (kovaaks_id);


--
-- Name: global_kovaaks_accounts global_kovaaks_accounts_steam_id_key; Type: CONSTRAINT; Schema: accounts; Owner: postgres
--

ALTER TABLE ONLY accounts.global_kovaaks_accounts
    ADD CONSTRAINT global_kovaaks_accounts_steam_id_key UNIQUE (steam_id);


--
-- Name: global_valorant_accounts global_valorant_accounts_pkey; Type: CONSTRAINT; Schema: accounts; Owner: postgres
--

ALTER TABLE ONLY accounts.global_valorant_accounts
    ADD CONSTRAINT global_valorant_accounts_pkey PRIMARY KEY (valorant_id);


--
-- Name: guild_leaderboard_settings guild_leaderboard_settings_pkey; Type: CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_leaderboard_settings
    ADD CONSTRAINT guild_leaderboard_settings_pkey PRIMARY KEY (guild_id, leaderboard_type);


--
-- Name: guild_membership guild_membership_pkey; Type: CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_membership
    ADD CONSTRAINT guild_membership_pkey PRIMARY KEY (guild_id, discord_id);


--
-- Name: guild_settings guild_settings_pkey; Type: CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_settings
    ADD CONSTRAINT guild_settings_pkey PRIMARY KEY (guild_id);


--
-- Name: guilds guilds_pkey; Type: CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guilds
    ADD CONSTRAINT guilds_pkey PRIMARY KEY (guild_id);


--
-- Name: dojo_advanced_playlist dojo_advanced_playlist_pkey; Type: CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.dojo_advanced_playlist
    ADD CONSTRAINT dojo_advanced_playlist_pkey PRIMARY KEY (profile_id);


--
-- Name: dojo_balanced_playlist dojo_balanced_playlist_pkey; Type: CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.dojo_balanced_playlist
    ADD CONSTRAINT dojo_balanced_playlist_pkey PRIMARY KEY (profile_id);


--
-- Name: valorant_dm valorant_dm_pkey; Type: CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.valorant_dm
    ADD CONSTRAINT valorant_dm_pkey PRIMARY KEY (profile_id);


--
-- Name: valorant_rank valorant_rank_pkey; Type: CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.valorant_rank
    ADD CONSTRAINT valorant_rank_pkey PRIMARY KEY (profile_id);


--
-- Name: voltaic_s5 voltaic_s5_pkey; Type: CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.voltaic_s5
    ADD CONSTRAINT voltaic_s5_pkey PRIMARY KEY (profile_id);


--
-- Name: voltaic_val_s1 voltaic_val_s1_pkey; Type: CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.voltaic_val_s1
    ADD CONSTRAINT voltaic_val_s1_pkey PRIMARY KEY (profile_id);


--
-- Name: aimlabs_profiles aimlabs_profiles_pkey; Type: CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.aimlabs_profiles
    ADD CONSTRAINT aimlabs_profiles_pkey PRIMARY KEY (profile_id);


--
-- Name: discord_profiles discord_profiles_pkey; Type: CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.discord_profiles
    ADD CONSTRAINT discord_profiles_pkey PRIMARY KEY (discord_id);


--
-- Name: kovaaks_profiles kovaaks_profiles_pkey; Type: CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.kovaaks_profiles
    ADD CONSTRAINT kovaaks_profiles_pkey PRIMARY KEY (profile_id);


--
-- Name: valorant_profiles valorant_profiles_pkey; Type: CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.valorant_profiles
    ADD CONSTRAINT valorant_profiles_pkey PRIMARY KEY (profile_id);


--
-- Name: global_aimlabs_accounts_last_updated_idx; Type: INDEX; Schema: accounts; Owner: postgres
--

CREATE INDEX global_aimlabs_accounts_last_updated_idx ON accounts.global_aimlabs_accounts USING btree (last_updated);


--
-- Name: global_kovaaks_accounts_last_updated_idx; Type: INDEX; Schema: accounts; Owner: postgres
--

CREATE INDEX global_kovaaks_accounts_last_updated_idx ON accounts.global_kovaaks_accounts USING btree (last_updated);


--
-- Name: global_valorant_accounts_last_updated_idx; Type: INDEX; Schema: accounts; Owner: postgres
--

CREATE INDEX global_valorant_accounts_last_updated_idx ON accounts.global_valorant_accounts USING btree (last_updated);


--
-- Name: guild_leaderboard_settings_is_enabled_idx; Type: INDEX; Schema: guilds; Owner: postgres
--

CREATE INDEX guild_leaderboard_settings_is_enabled_idx ON guilds.guild_leaderboard_settings USING btree (is_enabled);


--
-- Name: guild_settings_leaderboard_channel_id_idx; Type: INDEX; Schema: guilds; Owner: postgres
--

CREATE INDEX guild_settings_leaderboard_channel_id_idx ON guilds.guild_settings USING btree (leaderboard_channel_id);


--
-- Name: guild_settings_leaderboard_message_id_idx; Type: INDEX; Schema: guilds; Owner: postgres
--

CREATE INDEX guild_settings_leaderboard_message_id_idx ON guilds.guild_settings USING btree (leaderboard_message_id);


--
-- Name: aimlabs_profiles_discord_id_guild_id_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE UNIQUE INDEX aimlabs_profiles_discord_id_guild_id_idx ON profiles.aimlabs_profiles USING btree (discord_id, guild_id);


--
-- Name: aimlabs_profiles_guild_id_aimlabs_id_active_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE UNIQUE INDEX aimlabs_profiles_guild_id_aimlabs_id_active_idx ON profiles.aimlabs_profiles USING btree (guild_id, aimlabs_id) WHERE (is_active = true);


--
-- Name: aimlabs_profiles_is_active_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE INDEX aimlabs_profiles_is_active_idx ON profiles.aimlabs_profiles USING btree (is_active);


--
-- Name: kovaaks_profiles_discord_id_guild_id_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE UNIQUE INDEX kovaaks_profiles_discord_id_guild_id_idx ON profiles.kovaaks_profiles USING btree (discord_id, guild_id);


--
-- Name: kovaaks_profiles_guild_id_kovaaks_id_active_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE UNIQUE INDEX kovaaks_profiles_guild_id_kovaaks_id_active_idx ON profiles.kovaaks_profiles USING btree (guild_id, kovaaks_id) WHERE (is_active = true);


--
-- Name: kovaaks_profiles_is_active_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE INDEX kovaaks_profiles_is_active_idx ON profiles.kovaaks_profiles USING btree (is_active);


--
-- Name: valorant_profiles_discord_id_guild_id_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE UNIQUE INDEX valorant_profiles_discord_id_guild_id_idx ON profiles.valorant_profiles USING btree (discord_id, guild_id);


--
-- Name: valorant_profiles_guild_id_valorant_id_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE UNIQUE INDEX valorant_profiles_guild_id_valorant_id_idx ON profiles.valorant_profiles USING btree (guild_id, valorant_id) WHERE (is_active = true);


--
-- Name: valorant_profiles_is_active_idx; Type: INDEX; Schema: profiles; Owner: postgres
--

CREATE INDEX valorant_profiles_is_active_idx ON profiles.valorant_profiles USING btree (is_active);


--
-- Name: guild_leaderboard_settings guild_leaderboard_settings_guild_id_fkey; Type: FK CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_leaderboard_settings
    ADD CONSTRAINT guild_leaderboard_settings_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES guilds.guilds(guild_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: guild_membership guild_membership_discord_id_fkey; Type: FK CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_membership
    ADD CONSTRAINT guild_membership_discord_id_fkey FOREIGN KEY (discord_id) REFERENCES profiles.discord_profiles(discord_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: guild_membership guild_membership_guild_id_fkey; Type: FK CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_membership
    ADD CONSTRAINT guild_membership_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES guilds.guilds(guild_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: guild_settings guild_settings_guild_id_fkey; Type: FK CONSTRAINT; Schema: guilds; Owner: postgres
--

ALTER TABLE ONLY guilds.guild_settings
    ADD CONSTRAINT guild_settings_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES guilds.guilds(guild_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: dojo_advanced_playlist dojo_advanced_playlist_profile_id_fkey; Type: FK CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.dojo_advanced_playlist
    ADD CONSTRAINT dojo_advanced_playlist_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES profiles.aimlabs_profiles(profile_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: dojo_balanced_playlist dojo_balanced_playlist_profile_id_fkey; Type: FK CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.dojo_balanced_playlist
    ADD CONSTRAINT dojo_balanced_playlist_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES profiles.aimlabs_profiles(profile_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: valorant_dm valorant_dm_profile_id_fkey; Type: FK CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.valorant_dm
    ADD CONSTRAINT valorant_dm_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES profiles.valorant_profiles(profile_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: valorant_rank valorant_rank_profile_id_fkey; Type: FK CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.valorant_rank
    ADD CONSTRAINT valorant_rank_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES profiles.valorant_profiles(profile_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: voltaic_s5 voltaic_s5_profile_id_fkey; Type: FK CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.voltaic_s5
    ADD CONSTRAINT voltaic_s5_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES profiles.kovaaks_profiles(profile_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: voltaic_val_s1 voltaic_val_s1_profile_id_fkey; Type: FK CONSTRAINT; Schema: leaderboards; Owner: postgres
--

ALTER TABLE ONLY leaderboards.voltaic_val_s1
    ADD CONSTRAINT voltaic_val_s1_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES profiles.aimlabs_profiles(profile_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: aimlabs_profiles aimlabs_profiles_aimlabs_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.aimlabs_profiles
    ADD CONSTRAINT aimlabs_profiles_aimlabs_id_fkey FOREIGN KEY (aimlabs_id) REFERENCES accounts.global_aimlabs_accounts(aimlabs_id) ON DELETE RESTRICT;


--
-- Name: aimlabs_profiles aimlabs_profiles_guild_id_discord_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.aimlabs_profiles
    ADD CONSTRAINT aimlabs_profiles_guild_id_discord_id_fkey FOREIGN KEY (guild_id, discord_id) REFERENCES guilds.guild_membership(guild_id, discord_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: kovaaks_profiles kovaaks_profiles_guild_id_discord_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.kovaaks_profiles
    ADD CONSTRAINT kovaaks_profiles_guild_id_discord_id_fkey FOREIGN KEY (guild_id, discord_id) REFERENCES guilds.guild_membership(guild_id, discord_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: kovaaks_profiles kovaaks_profiles_kovaaks_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.kovaaks_profiles
    ADD CONSTRAINT kovaaks_profiles_kovaaks_id_fkey FOREIGN KEY (kovaaks_id) REFERENCES accounts.global_kovaaks_accounts(kovaaks_id) ON DELETE RESTRICT;


--
-- Name: valorant_profiles valorant_profiles_guild_id_discord_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.valorant_profiles
    ADD CONSTRAINT valorant_profiles_guild_id_discord_id_fkey FOREIGN KEY (guild_id, discord_id) REFERENCES guilds.guild_membership(guild_id, discord_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: valorant_profiles valorant_profiles_valorant_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: postgres
--

ALTER TABLE ONLY profiles.valorant_profiles
    ADD CONSTRAINT valorant_profiles_valorant_id_fkey FOREIGN KEY (valorant_id) REFERENCES accounts.global_valorant_accounts(valorant_id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

