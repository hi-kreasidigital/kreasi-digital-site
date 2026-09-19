# Panduan Publish Website Kreasi Digital

Urutannya penting — ikuti dari atas ke bawah. Total sekitar 30–45 menit.

Peran tiap layanan:
- **Airtable** — tempat kamu edit semua konten (artikel, studi kasus, teks section, kontak)
- **GitHub** — tempat file website disimpan, sekaligus mesin yang build ulang situs otomatis
- **GitHub Pages** — hosting gratis situsnya
- **Supabase** — khusus menampung pendaftar newsletter dari form publik

---

## TAHAP 1 — Siapkan repository GitHub

1. Login ke github.com, klik **+** (kanan atas) → **New repository**.
2. **Repository name**: `kreasi-digital` (atau nama lain, catat baik-baik — akan dipakai di Tahap 4).
3. Pilih **Public** (wajib, supaya GitHub Pages & Actions gratis).
4. Jangan centang "Add a README". Klik **Create repository**.
5. Di halaman repo yang baru dibuat, klik **uploading an existing file**.
6. Ekstrak `kreasi-digital-site.zip`, lalu **drag semua isinya** (bukan foldernya, tapi isi di dalamnya) ke jendela upload.
   - Pastikan folder `scripts/` dan `.github/` ikut terupload.
   - Kalau `.github/` tidak ikut ter-drag (kadang tersembunyi), lihat catatan di bawah.
7. Klik **Commit changes**.

**Kalau folder `.github/` tidak mau terupload:** di repo, klik **Add file → Create new file**, lalu ketik nama file persis: `.github/workflows/rebuild.yml` (GitHub otomatis bikin foldernya), paste isi file `rebuild.yml` dari zip, lalu commit.

8. **Upload gambar-gambar kamu.** File gambar lama (logo.png, hero-illustration.png, foto portofolio) tidak ada di zip. Upload semuanya ke root repo dengan cara yang sama, pakai nama file yang sama seperti sebelumnya.

---

## TAHAP 2 — Ambil token Airtable

1. Buka https://airtable.com/create/tokens → **Create new token**.
2. **Name**: `kreasi-digital-website`
3. **Scopes**: tambahkan `data.records:read` saja (cukup baca — script tidak perlu menulis ke Airtable).
4. **Access**: pilih base **Kreasi Digital**.
5. Klik **Create token**, lalu **salin tokennya sekarang** (hanya ditampilkan sekali). Simpan sementara di notepad.

Base ID kamu sudah diketahui: `appTgtEPUl5kIRHvv`

---

## TAHAP 3 — Setup Supabase untuk newsletter

1. Buka https://supabase.com → **Start your project** → login dengan GitHub.
2. **New project**:
   - Name: `kreasi-digital`
   - Database password: bikin password kuat, simpan (tidak dipakai di website, tapi perlu untuk akses DB)
   - Region: **Southeast Asia (Singapore)** — paling dekat ke Indonesia
   - Plan: **Free**
3. Tunggu project selesai dibuat (~2 menit).
4. Buka menu kiri **SQL Editor** → **New query**.
5. Buka file `supabase-setup.sql` dari zip, **copy seluruh isinya**, paste ke editor, klik **Run**.
   - Harus muncul "Success. No rows returned". Kalau error, screenshot errornya.
6. Buka **Project Settings** (ikon gerigi) → **API**. Catat dua hal:
   - **Project URL** → contoh `https://abcdefgh.supabase.co`
   - **anon public** key → string panjang diawali `eyJ...`

**Kenapa anon key aman dipajang publik?** Karena SQL di langkah 5 mengaktifkan Row Level Security dan hanya memberi izin INSERT. Dengan anon key, orang cuma bisa mendaftarkan email — tidak bisa membaca, mengubah, atau menghapus daftar subscriber kamu.

---

## TAHAP 4 — Masukkan semua kunci ke GitHub Secrets

Di repo GitHub kamu: **Settings** (tab repo, bukan settings akun) → menu kiri **Secrets and variables** → **Actions** → tombol **New repository secret**.

Tambahkan satu per satu (nama harus persis):

| Name | Secret value |
|---|---|
| `AIRTABLE_API_KEY` | token dari Tahap 2 |
| `AIRTABLE_BASE_ID` | `appTgtEPUl5kIRHvv` |
| `SITE_BASE_URL` | `https://USERNAME.github.io/kreasi-digital` |
| `BASE_PATH` | `/kreasi-digital` |
| `SUPABASE_URL` | Project URL dari Tahap 3 |
| `SUPABASE_ANON_KEY` | anon public key dari Tahap 3 |

Ganti `USERNAME` dengan username GitHub kamu, dan `kreasi-digital` dengan nama repo kamu kalau berbeda.

**`BASE_PATH` itu penting.** Karena URL gratis GitHub Pages berbentuk `username.github.io/nama-repo/`, semua link internal harus diberi awalan nama repo. Tanpa ini, semua menu dan tombol di situs akan mengarah ke halaman 404.

---

## TAHAP 5 — Aktifkan GitHub Pages

1. Di repo: **Settings** → menu kiri **Pages**.
2. **Source**: pilih **Deploy from a branch**.
3. **Branch**: `main`, folder: `/ (root)`. Klik **Save**.
4. Tunggu 1–2 menit, refresh halaman. Akan muncul link situsmu di bagian atas:
   `https://USERNAME.github.io/kreasi-digital/`

---

## TAHAP 6 — Jalankan build pertama

1. Di repo: tab **Actions**.
2. Kalau muncul tombol hijau "I understand my workflows, enable them" — klik.
3. Di daftar kiri, klik workflow **Rebuild site from Airtable**.
4. Klik **Run workflow** (kanan) → **Run workflow**.
5. Tunggu ~1 menit. Kalau centang hijau, berhasil. Kalau merah, klik jobnya untuk lihat pesan errornya.

Buka URL situsmu. Semua halaman sekarang sudah di-generate dari Airtable.

**Setelah ini, alurnya jadi begini:** kamu edit konten di Airtable → tunggu maksimal 15 menit (workflow jalan otomatis tiap 15 menit) → perubahan muncul di situs. Kalau tidak mau menunggu, tinggal ulangi langkah 3–4 di atas untuk memicu manual.

---

## TAHAP 7 — Daftarkan ke Google

1. **Google Search Console** (https://search.google.com/search-console):
   - Add property → pilih **URL prefix** → masukkan URL GitHub Pages kamu
   - Verifikasi dengan metode **HTML tag**: copy tag meta yang diberikan, lalu tempelkan ke file `scripts/generate_from_airtable.py` di dalam fungsi `page_shell` (di bagian `<head>`), commit, dan jalankan ulang workflow. Atau minta bantuan saya untuk ini.
   - Setelah terverifikasi: menu **Sitemaps** → submit `sitemap.xml`
2. **Google Business Profile** (https://business.google.com) — ini yang paling berpengaruh untuk pencarian "jasa website Bali" / "jasa kasir digital Malang". Daftarkan usaha kamu, isi area layanan Bali & Malang, dan cantumkan URL situsmu.

---

## NANTI: Pindah ke domain berbayar

Saat domain sudah dibeli, cuma 4 langkah:

1. Di penyedia domain, tambahkan DNS record:
   - 4 record **A** untuk root domain (`@`) ke: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - 1 record **CNAME** untuk `www` ke `USERNAME.github.io`
2. Di repo: **Settings → Pages → Custom domain**, isi domain kamu, **Save**. Centang **Enforce HTTPS** setelah sertifikat siap (bisa perlu hingga 24 jam).
3. Di **Settings → Secrets → Actions**, ubah dua secret:
   - `SITE_BASE_URL` → `https://www.domainkamu.com`
   - `BASE_PATH` → **kosongkan isinya** (hapus nilainya, simpan sebagai string kosong)
4. Jalankan ulang workflow (Actions → Run workflow). Semua link internal dan canonical URL otomatis menyesuaikan.

Setelah itu, daftarkan ulang domain baru di Google Search Console sebagai property terpisah.

---

## Cek hasil & troubleshooting

**Cek newsletter jalan:** buka halaman Beranda atau Blog situsmu, masukkan email uji, klik Daftar. Lalu cek di Supabase → **Table Editor** → `newsletter_subscribers`. Emailnya harus muncul di situ.

**Semua link 404?** `BASE_PATH` salah atau belum diisi. Nilainya harus `/nama-repo` persis, diawali garis miring, tanpa garis miring di akhir.

**Workflow merah di Actions?** Klik job yang gagal → baca log. Biasanya: token Airtable salah/kadaluarsa, atau nama secret typo.

**Gambar tidak muncul?** File gambar belum diupload ke repo, atau nama filenya beda (huruf besar/kecil berpengaruh di GitHub Pages).

**Konten di Airtable sudah diubah tapi situs belum berubah?** Workflow jalan tiap 15 menit. Untuk artikel dan studi kasus, pastikan kolom **Status** sudah diset ke **Published**.
