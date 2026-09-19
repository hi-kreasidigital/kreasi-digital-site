-- =====================================================================
-- SETUP SUPABASE UNTUK NEWSLETTER KREASI DIGITAL
-- Jalankan sekali saja di Supabase Dashboard > SQL Editor > New query
-- =====================================================================

-- 1. Tabel penampung pendaftar newsletter
create table if not exists public.newsletter_subscribers (
    id              bigint generated always as identity primary key,
    email           text not null unique,
    sumber_halaman  text,
    created_at      timestamptz not null default now()
);

-- 2. Aktifkan Row Level Security.
--    Tanpa ini, anon key bisa BACA SEMUA email -- tidak boleh.
alter table public.newsletter_subscribers enable row level security;

-- 3. Hanya izinkan INSERT dari pengunjung anonim (form di website).
--    Tidak ada policy SELECT/UPDATE/DELETE, jadi anon key TIDAK BISA
--    membaca, mengubah, atau menghapus data. Ini yang bikin aman
--    menaruh anon key di HTML publik.
drop policy if exists "anon boleh daftar newsletter" on public.newsletter_subscribers;
create policy "anon boleh daftar newsletter"
    on public.newsletter_subscribers
    for insert
    to anon
    with check (true);

-- =====================================================================
-- Cara lihat daftar subscriber:
-- Supabase Dashboard > Table Editor > newsletter_subscribers
-- (kamu login sebagai pemilik project, jadi bisa lihat semuanya)
--
-- Untuk export ke Airtable: Table Editor > tombol Export > CSV,
-- lalu import CSV itu ke tabel "CMS - Newsletter Subscribers".
-- =====================================================================
