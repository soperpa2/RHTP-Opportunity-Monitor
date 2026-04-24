create extension if not exists pgcrypto;

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  state text not null,
  state_abbreviation text not null,
  agency text not null default 'State Procurement Office',
  agency_type text not null default 'procurement_portal',
  url text not null unique,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists raw_opportunities (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id),
  state text,
  agency text,
  title text not null,
  url text not null unique,
  description text,
  raw_text text,
  ingested_at timestamptz default now()
);
