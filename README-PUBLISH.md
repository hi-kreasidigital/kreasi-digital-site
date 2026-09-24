# Panduan Publish Situs Kreasi Digital (Gratis, Kecuali Domain)

> **Catatan:** dokumen ini adalah catatan awal proyek. Untuk langkah setup yang paling baru dan lengkap (termasuk `BASE_PATH` dan newsletter), ikuti **`PANDUAN-PUBLISH.md`**. Bagian 1 di bawah (script `build.py`, `pages.py`, dll.) berasal dari versi sebelum auto-publish Airtable dan sudah tidak dipakai.

## 1. Sebelum upload
- Ganti `BASE_URL` di `build.py` (sudah dipakai di semua canonical/OG/sitemap) dengan domain final kamu, lalu jalankan ulang `python3 pages.py && python3 case_studies.py && python3 blog.py` dan buat ulang `sitemap.xml`.
- Taruh semua file gambar yang direferensikan (logo.png, hero-illustration.png, tara.jpeg, mattel.jpeg, tattoo-in-bali.jpg, pride-on.jpg, bali-island-driver.jpg, aussie-souvenirs.jpg, app-illustration.png, nota-pos.jpg, outreach-cafe.jpg, rekap-warga.jpg) di folder yang sama dengan file HTML ini (root repo). Tambahkan juga `og-cover.jpg` (1200x630px) untuk preview link di WhatsApp/social media.

## 2. Hosting gratis: GitHub Pages
1. Buat repository baru di GitHub, misalnya `kreasi-digital-site`.
2. Upload semua file di folder ini (HTML + gambar) ke root repo tsb.
3. Buka **Settings > Pages** di repo, pilih branch `main` folder `/root`, klik Save.
4. Situs akan aktif di `https://<username>.github.io/<nama-repo>/` dalam beberapa menit.
5. (Opsional, kalau beli domain sendiri) Tambahkan file `CNAME` berisi domain kamu (misal `kreasidigital.id`), lalu arahkan DNS domain ke GitHub Pages sesuai [panduan resmi GitHub](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site).

Alternatif hosting gratis lain: **Cloudflare Pages** atau **Netlify** — caranya mirip, tinggal hubungkan repo GitHub kamu dan deploy otomatis, keduanya juga gratis untuk situs statis seperti ini.

## 3. Supaya bisa rangking di pencarian (gratis)
1. **Google Search Console** (gratis) — daftarkan domain kamu, verifikasi kepemilikan, lalu submit `sitemap.xml` (`https://domainkamu.com/sitemap.xml`).
2. **Bing Webmaster Tools** (gratis) — sama, submit sitemap juga supaya terindeks di Bing.
3. **Google Business Profile** (gratis, PENTING untuk keyword lokal seperti "jasa website Bali" / "jasa kasir digital Malang") — daftarkan usaha kamu, isi kategori, area layanan (Bali & Malang), dan link ke website. Ini paling berpengaruh untuk pencarian lokal.
4. Pastikan **nama, alamat/area, dan nomor kontak (NAP)** konsisten di semua tempat: website, Google Business Profile, dan media sosial.
5. Rutin isi halaman `/blog.html` dengan artikel baru — konten yang terus update membantu ranking jangka panjang.
6. Minta beberapa klien memberi ulasan (Google review) dan, kalau memungkinkan, minta mereka mencantumkan link balik (backlink) ke halaman studi kasus terkait — backlink dari situs relevan membantu otoritas domain kamu.
7. Cek kecepatan & mobile-friendliness lewat [PageSpeed Insights](https://pagespeed.web.dev/) (gratis) setelah live.

## 4. Struktur halaman yang sudah dibuat
- `index.html` — Beranda
- `jasa-website-bali.html`, `jasa-kasir-digital-malang.html`, `dashboard-sistem-umkm.html` — halaman layanan terpisah
- `studi-kasus-*.html` (7 halaman) — studi kasus tiap portofolio, dengan link keluar ke domain klien ditandai `rel="noopener noreferrer nofollow"` dan `target="_blank"` sehingga pengunjung tidak "kabur" dari situs kamu (link internal ke studi kasus tetap jadi tujuan utama).
- `blog.html` + 2 artikel edukasi UMKM
- `sitemap.xml`, `robots.txt`

Semua halaman sudah punya `<title>` dan `<meta name="description">` yang unik, tag Open Graph, serta data terstruktur (schema.org) untuk ProfessionalService/Service/Article — ini membantu Google memahami konten tiap halaman.

## 5. Dashboard edit konten (Airtable) + auto-publish

Base Airtable "Kreasi Digital" sekarang punya 5 tabel baru berawalan **"CMS -"**:

- **CMS - Pengaturan Situs** — satu baris = satu "section" (header, footer, hero beranda, tentang kami, hero tiap halaman layanan, dst). Kolom: Judul, Paragraf/Deskripsi, Gambar, Teks Tombol, Link Tombol.
- **CMS - Kontak** — satu baris data kontak resmi (email, WhatsApp, area layanan, Instagram, Facebook).
- **CMS - Studi Kasus** — tambah baris baru di sini untuk menambah portofolio. Set **Status = Published** supaya tampil di situs.
- **CMS - Artikel Blog** — tambah baris baru untuk artikel edukasi UMKM baru. Set **Status = Published** supaya tampil.
- **CMS - Newsletter Subscribers** — semua pendaftar dari form newsletter di situs (Beranda & Blog) otomatis tercatat di sini lewat Airtable Automation **"Newsletter: simpan pendaftar dari website"**. Email ganda dan kiriman bot otomatis disaring. Cara setup-nya ada di `PANDUAN-PUBLISH.md` Tahap 3.
- **CMS - Proses Kerja** — langkah-langkah "cara kami bekerja" di tiap halaman layanan (kolom Halaman menentukan tampil di halaman mana, Urutan menentukan posisinya). Sudah saya isi 4 langkah standar untuk tiap halaman — tinggal ubah teksnya atau tambah/kurangi baris.
- **CMS - FAQ Layanan** — pertanyaan & jawaban per halaman layanan, sama seperti di atas pakai kolom Halaman + Urutan. Sudah saya isi 3 FAQ untuk tiap halaman layanan.

Sekarang ketiga halaman layanan (`jasa-website-bali.html`, `jasa-kasir-digital-malang.html`, `dashboard-sistem-umkm.html`) di-generate PENUH oleh script — bukan cuma bagian hero lagi. Studi kasus yang tampil di tiap halaman layanan juga otomatis ditarik berdasarkan kolom **Kategori** di tabel CMS - Studi Kasus (Website / Kasir Digital (POS) / Dashboard), jadi kalau kamu tambah studi kasus baru dengan kategori yang sesuai, otomatis muncul juga di halaman layanan terkait.

**Cara kerja auto-publish:** ada script `scripts/generate_from_airtable.py` yang membaca ke-4 tabel di atas lewat Airtable API, lalu menulis ulang `index.html`, `blog.html`, semua `studi-kasus-*.html`, dan semua `artikel-*.html` — termasuk meta description unik dan struktur schema.org yang sama seperti sebelumnya. Header, footer, dan kontak di SEMUA halaman (termasuk 3 halaman layanan) juga ikut diperbarui dari tabel Pengaturan Situs & Kontak.

Supaya ini jalan otomatis tiap kamu update Airtable, sudah disiapkan **GitHub Actions** di `.github/workflows/rebuild.yml` yang jalan tiap 15 menit, mengecek Airtable, lalu commit & push perubahan kalau ada — semuanya gratis untuk repo publik.

**Setup sekali saja (sekitar 10 menit):**
1. Buka https://airtable.com/create/tokens, buat **Personal Access Token** baru dengan scope `data.records:read`, akses ke base "Kreasi Digital" saja.
2. Di repo GitHub kamu, buka **Settings → Secrets and variables → Actions**, tambahkan 4 secret:
   - `AIRTABLE_API_KEY` — token dari langkah 1
   - `AIRTABLE_BASE_ID` — `appTgtEPUl5kIRHvv`
   - `SITE_BASE_URL` — URL situs lengkap tanpa garis miring di akhir, misal `https://hi-kreasidigital.github.io/kreasi-digital-site` (nanti `https://www.kreasidigital.id` setelah pakai domain sendiri)
   - `BASE_PATH` — `/nama-repo` selama masih pakai URL GitHub Pages gratis (misal `/kreasi-digital-site`); kosongkan setelah pindah ke domain sendiri
3. Pastikan file `scripts/generate_from_airtable.py` dan `.github/workflows/rebuild.yml` ada di root repo (folder `.github/workflows/` harus persis seperti itu).
4. Selesai — sekarang tiap kamu tambah/edit baris di Airtable (dan set Status = Published), dalam ±15 menit halamannya otomatis muncul di situs, lengkap dengan meta description unik.

**Batasan yang masih ada:**
- Bagian "Yang Kamu Dapatkan" (daftar fitur) dan kalimat pembuka tiap halaman layanan masih statis di kode (bukan permintaan awal untuk dieditkan) — kalau nanti mau itu juga full-editable, tinggal minta lagi.
- Gambar yang di-upload lewat kolom "Gambar" di Airtable akan memakai link dari server Airtable. Ini praktis, tapi kalau suatu saat ingin lebih permanen, gambar bisa dipindah ke folder repo dan direferensikan langsung.
- Newsletter: form custom di situs sudah tersambung ke Airtable **tanpa** menaruh token Airtable di halaman publik — form mengirim ke webhook Airtable Automation, dan URL webhook itu hanya bisa menambah pendaftar. Karena webhook Airtable tidak mendukung CORS, form tidak bisa membaca balasan Airtable, jadi pesan sukses selalu tampil setelah kiriman berangkat. Yang belum ada: alur untuk benar-benar mengirim newsletter ke para subscriber.
