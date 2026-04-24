create extension if not exists pgcrypto;

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  state text not null,
  state_abbreviation char(2) not null,
  agency text not null default 'State Procurement Office',
  agency_type text not null default 'procurement_portal',
  url text not null unique,
  page_name text,
  likely_content_type text default 'procurement_portal',
  why_monitor_this text,
  priority text not null default 'High',
  notes text,
  is_js_heavy_likely text default 'yes',
  requires_vendor_login_likely text default 'maybe',
  crawl_frequency text not null default 'daily',
  manual_verification_needed text default 'no',
  source_priority integer not null default 1,
  follow_links text not null default 'yes',
  max_links_to_follow integer not null default 10,
  active boolean not null default true,
  last_crawled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists crawl_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'running',
  sources_attempted integer default 0,
  pages_visited integer default 0,
  opportunities_found integer default 0,
  errors jsonb default '[]'::jsonb
);

create table if not exists raw_opportunities (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id) on delete set null,
  crawl_run_id uuid references crawl_runs(id) on delete set null,
  state text,
  agency text,
  title text not null,
  url text not null unique,
  posted_date date,
  due_date date,
  description text,
  raw_text text,
  source_url text,
  content_hash text,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  ingested_at timestamptz not null default now()
);

create table if not exists scored_opportunities (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid not null references raw_opportunities(id) on delete cascade,
  matched_keywords text[] default '{}',
  matched_phrases text[] default '{}',
  excluded_terms text[] default '{}',
  relevance_score integer not null default 0,
  strategic_fit_score integer not null default 0,
  include_for_review text not null default 'no',
  explanation text,
  created_at timestamptz not null default now(),
  unique(opportunity_id)
);

create table if not exists review_pipeline (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid not null references raw_opportunities(id) on delete cascade,
  review_status text not null default 'new',
  pursue_status text,
  assigned_to text,
  notes text,
  last_reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(opportunity_id)
);

create or replace view dashboard_opportunities as
select
  r.id, r.state, r.agency, r.title, r.url, r.posted_date, r.due_date, r.description, r.first_seen_at,
  s.relevance_score, s.strategic_fit_score, s.include_for_review, s.matched_phrases, s.matched_keywords, s.excluded_terms,
  coalesce(p.review_status, 'new') as review_status, p.pursue_status, p.assigned_to, p.notes
from raw_opportunities r
left join scored_opportunities s on r.id = s.opportunity_id
left join review_pipeline p on r.id = p.opportunity_id;

create index if not exists idx_raw_opps_state on raw_opportunities(state);
create index if not exists idx_raw_opps_due_date on raw_opportunities(due_date);
create index if not exists idx_scores_include on scored_opportunities(include_for_review);
create index if not exists idx_scores_relevance on scored_opportunities(relevance_score desc);
