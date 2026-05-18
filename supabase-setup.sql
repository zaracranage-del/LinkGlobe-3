-- ═══════════════════════════════════════════════════════════════
-- LinkGlobe — Full Database Setup
-- Run this in Supabase → SQL Editor → New query → Run
-- ═══════════════════════════════════════════════════════════════

-- ── 1. SIGNUPS (creator profiles) ───────────────────────────────
create table if not exists signups (
  id            bigserial primary key,
  created_at    timestamptz default now(),
  email         text unique not null,
  name          text,
  handle        text unique not null,
  bio           text,
  instagram     text,
  tiktok        text,
  plan          text default 'free',  -- 'free' | 'creator' | 'pro'
  brand_color   text default '#4f46e5',
  avatar_url    text,
  custom_domain text,
  -- Affiliate tags per country
  tag_au  text, tag_us  text, tag_uk  text,
  tag_ca  text, tag_de  text, tag_jp  text,
  tag_fr  text, tag_it  text, tag_es  text,
  tag_nl  text, tag_sg  text, tag_mx  text, tag_in text,
  -- Storefront appearance
  sf_theme     text default 'noir',
  sf_font      text default 'serif',
  sf_btn_style text default 'rounded',
  sf_btn_color text default '#0a0a0a',
  sf_font_color text default '#ffffff',
  sf_bg_color  text,
  sf_bg_image  text
);

-- ── 2. PRODUCTS ─────────────────────────────────────────────────
create table if not exists products (
  id           bigserial primary key,
  created_at   timestamptz default now(),
  handle       text not null references signups(handle) on update cascade on delete cascade,
  user_email   text not null,
  name         text,
  store        text,           -- 'amazon' | 'brand'
  store_label  text,
  emoji        text,
  image        text,
  original_url text,
  geo_link     text
);
create index if not exists products_handle_idx on products(handle);

-- ── 3. CLICKS (storefront product clicks — client-side) ─────────
create table if not exists clicks (
  id          bigserial primary key,
  created_at  timestamptz default now(),
  handle      text not null,
  product_id  bigint references products(id) on delete set null,
  store       text,
  geo_link    text,
  country     text,
  device      text,
  os          text,
  browser     text,
  referrer    text
);
create index if not exists clicks_handle_idx on clicks(handle);

-- ── 4. LINK_CLICKS (redirect API clicks — server-side) ──────────
create table if not exists link_clicks (
  id          bigserial primary key,
  created_at  timestamptz default now(),
  handle      text,
  asin        text,
  country     text,
  store       text,
  referrer    text,
  clicked_at  timestamptz default now()
);
create index if not exists link_clicks_handle_idx on link_clicks(handle);

-- ── 5. COLLECTIONS ───────────────────────────────────────────────
create table if not exists collections (
  id          bigserial primary key,
  created_at  timestamptz default now(),
  handle      text not null,
  user_email  text,
  name        text not null,
  slug        text not null,
  unique(handle, slug)
);
create index if not exists collections_handle_idx on collections(handle);

-- ── 6. COLLECTION_PRODUCTS (junction) ───────────────────────────
create table if not exists collection_products (
  id            bigserial primary key,
  collection_id bigint not null references collections(id) on delete cascade,
  product_id    bigint not null references products(id) on delete cascade,
  unique(collection_id, product_id)
);

-- ── 7. AFFILIATE_PROGRAMS ────────────────────────────────────────
create table if not exists affiliate_programs (
  id           bigserial primary key,
  created_at   timestamptz default now(),
  handle       text not null,
  user_email   text not null,
  program_name text not null,
  network      text,
  store_domain text,
  tag          text,
  tracking_url text
);
create index if not exists affiliate_programs_handle_idx on affiliate_programs(handle);

-- ═══════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════

-- Enable RLS on all tables
alter table signups           enable row level security;
alter table products          enable row level security;
alter table clicks            enable row level security;
alter table link_clicks       enable row level security;
alter table collections       enable row level security;
alter table collection_products enable row level security;
alter table affiliate_programs  enable row level security;

-- SIGNUPS: public read (for storefronts), auth write own row
create policy if not exists "public_read_signups"
  on signups for select using (true);
create policy if not exists "auth_insert_signups"
  on signups for insert with check (true);
create policy if not exists "auth_update_own_signup"
  on signups for update using (auth.jwt() ->> 'email' = email);
create policy if not exists "auth_delete_own_signup"
  on signups for delete using (auth.jwt() ->> 'email' = email);

-- PRODUCTS: public read, auth write own rows
create policy if not exists "public_read_products"
  on products for select using (true);
create policy if not exists "auth_insert_products"
  on products for insert with check (auth.jwt() ->> 'email' = user_email);
create policy if not exists "auth_update_own_products"
  on products for update using (auth.jwt() ->> 'email' = user_email);
create policy if not exists "auth_delete_own_products"
  on products for delete using (auth.jwt() ->> 'email' = user_email);

-- CLICKS: public insert (anyone clicking storefront), auth read own
create policy if not exists "public_insert_clicks"
  on clicks for insert with check (true);
create policy if not exists "public_read_clicks"
  on clicks for select using (true);

-- LINK_CLICKS: service role only (API writes, dashboard reads via anon)
create policy if not exists "public_read_link_clicks"
  on link_clicks for select using (true);
create policy if not exists "service_insert_link_clicks"
  on link_clicks for insert with check (true);

-- COLLECTIONS: public read, auth write own
create policy if not exists "public_read_collections"
  on collections for select using (true);
create policy if not exists "auth_insert_collections"
  on collections for insert with check (auth.jwt() ->> 'email' = user_email);
create policy if not exists "auth_update_own_collections"
  on collections for update using (auth.jwt() ->> 'email' = user_email);
create policy if not exists "auth_delete_own_collections"
  on collections for delete using (auth.jwt() ->> 'email' = user_email);

-- COLLECTION_PRODUCTS: public read, any auth insert/delete
create policy if not exists "public_read_collection_products"
  on collection_products for select using (true);
create policy if not exists "auth_manage_collection_products"
  on collection_products for all using (true);

-- AFFILIATE_PROGRAMS: auth read/write own
create policy if not exists "auth_read_own_programs"
  on affiliate_programs for select using (auth.jwt() ->> 'email' = user_email);
create policy if not exists "auth_insert_programs"
  on affiliate_programs for insert with check (auth.jwt() ->> 'email' = user_email);
create policy if not exists "auth_delete_own_programs"
  on affiliate_programs for delete using (auth.jwt() ->> 'email' = user_email);
