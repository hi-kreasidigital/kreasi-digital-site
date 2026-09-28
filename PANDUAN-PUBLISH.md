# Panduan Publish Website Kreasi Digital v3

Website ini dibangun otomatis dari Airtable dan di-hosting di GitHub Pages.

- **Airtable** (base **CMS Website Kreasi Digital**, ID `apptiqj9Z0vnDBJop`) adalah tempat semua konten diedit.
- **GitHub Actions** membaca Airtable setiap 15 menit, lalu membangun ulang halaman HTML.
- **GitHub Pages** menayangkan hasilnya.

Semua halaman di zip ini sudah dibangun dari isi Airtable per 28 September 2026, jadi website langsung tampil begitu file diunggah.

---

## 1. Unggah file ke repo yang sama

1. Buka repo `hi-kreasidigital/kreasi-digital-site` di GitHub.
2. Klik **Add file → Upload files**.
3. Ekstrak zip, lalu seret **seluruh isi folder** (bukan foldernya) ke jendela upload. File dengan nama sama akan tertimpa.
   - Pastikan folder `.github`, `scripts`, `assets`, `solusi`, `untuk`, `studi-kasus`, `blog`, dan `en` ikut terunggah.
   - Di Mac, folder berawalan titik (`.github`) tersembunyi. Tekan `Cmd + Shift + .` di Finder untuk menampilkannya.
4. Klik **Commit changes**.

File lama seperti `jasa-website-bali.html` dan `studi-kasus-nota-pos.html` sudah diganti dengan halaman pengalihan ke alamat barunya, jadi link lama yang sudah tersebar tetap berfungsi. Gambar lama di root repo (`tara.jpeg`, `pride-on.jpg`, dll.) tidak dipakai lagi dan boleh dihapus kapan saja.

## 2. Perbarui GitHub Secrets (wajib)

Buka **Settings → Secrets and variables → Actions** di repo.

| Secret | Isi |
| --- | --- |
| `AIRTABLE_BASE_ID` | `apptiqj9Z0vnDBJop` (ganti dari ID base lama) |
| `AIRTABLE_API_KEY` | Token Airtable yang punya akses ke base baru (lihat langkah 3) |
| `SITE_BASE_URL` | `https://hi-kreasidigital.github.io/kreasi-digital-site` |
| `BASE_PATH` | `/kreasi-digital-site` |
| `NEWSLETTER_WEBHOOK_URL` | Boleh dikosongkan (lihat bagian Newsletter) |

Selama `AIRTABLE_BASE_ID` masih berisi ID base lama, proses build otomatis akan gagal (tanda merah di tab Actions). Website tetap tampil normal karena halaman sudah dibangun, tapi perubahan di Airtable tidak akan terbit.

## 3. Beri token Airtable akses ke base baru

1. Buka https://airtable.com/create/tokens dan pilih token `kreasi-digital-website`.
2. Di bagian **Access**, tambahkan base **CMS Website Kreasi Digital**.
3. Scope cukup `data.records:read`.
4. Simpan. Token yang sama tidak perlu diganti di GitHub.

## 4. Jalankan build pertama

Buka tab **Actions → Rebuild site from Airtable → Run workflow**. Tunggu sampai centang hijau (sekitar 1 menit). Setelah itu, setiap perubahan di Airtable tayang otomatis dalam 15 menit.

---

## Cara mengedit konten di Airtable

| Tabel | Isinya | Muncul di |
| --- | --- | --- |
| **Teks Situs** | Semua teks tetap: menu, hero, judul section, tombol, footer, newsletter | Seluruh website |
| **Masalah Bisnis** | Satu baris = satu halaman solusi (10 halaman) | `/solusi/<slug>/` dan kartu di Beranda |
| **Audiens** | UMKM, Yayasan, Organisasi & Komunitas | `/untuk/<slug>/` |
| **Masalah per Audiens** | Baris tabel "Jika Anda mengalami... / Solusi" | Halaman `/untuk/` |
| **Studi Kasus** | Portofolio, dibuka dengan masalah bisnis klien | `/studi-kasus/<slug>/` |
| **Artikel Blog** | Artikel. Status **Ide** = rencana konten, tidak tampil | `/blog/<slug>/` |
| **FAQ** | Pertanyaan di halaman solusi, sekaligus FAQ schema untuk Google | Halaman solusi |
| **Proses Kerja**, **Tim**, **Kontak**, **Sosial Media** | Bagian-bagian Beranda dan footer | Beranda, footer |
| **Newsletter Subscribers** | Pendaftar newsletter (lihat catatan di bawah) | — |

Aturan penting:

- **Kolom ID dan EN.** Hampir setiap teks punya dua kolom: `... ID` untuk Bahasa Indonesia dan `... EN` untuk Bahasa Inggris. Kalau kolom EN kosong, halaman versi Inggris untuk baris itu tidak dibuat (atau memakai teks Indonesia untuk kolom kecil).
- **Status.** Hanya baris berstatus **Published** yang tampil. Ubah ke **Draft** untuk menyembunyikan; halamannya otomatis dihapus pada build berikutnya.
- **Slug.** Jangan ubah slug setelah halaman terbit. Slug yang berubah membuat link lama dan peringkat Google hilang.
- **Stabilo kuning.** Di tabel Teks Situs, kata yang diapit tanda bintang, misalnya `*masalah bisnis*`, diberi stabilo kuning.
- **Pilihan Solusi.** Satu baris per pilihan, dengan format `Judul :: penjelasan`.
- **Isi artikel.** Baris kosong untuk paragraf baru, `## ` untuk subjudul, `- ` untuk poin.
- **Gambar.** Unggah ke kolom Gambar Cover, Foto, atau Logo. Script mengunduh gambar itu ke repo, jadi link gambar tidak kedaluwarsa.

## Tombol bahasa ID / EN

Setiap halaman punya tombol **ID | EN** di menu atas yang menaut ke pasangan halamannya:

| Bahasa Indonesia | English |
| --- | --- |
| `/` | `/en/` |
| `/solusi/...` | `/en/solutions/...` |
| `/untuk/...` | `/en/for/...` |
| `/studi-kasus/...` | `/en/case-studies/...` |
| `/blog/...` | `/en/blog/...` |

Google diberi tahu pasangan ini lewat tag `hreflang` dan `sitemap.xml`, sehingga pencari berbahasa Inggris diarahkan ke versi Inggris.

## Newsletter

Form newsletter masih mengirim ke automation lama di base **Kreasi Digital** (sudah terbukti berjalan), jadi pendaftar baru tetap masuk ke tabel **CMS - Newsletter Subscribers** di base lama. Form sekarang juga mengirim kolom `bahasa` (id/en).

Untuk memindahkan newsletter ke base baru:

1. Di base **CMS Website Kreasi Digital**, buat automation dengan trigger **When webhook received**, lalu salin URL webhook-nya.
2. Kirim satu data contoh lewat Terminal di Mac:
   `curl -X POST -d "email=tes@contoh.com&sumber_halaman=Beranda&bahasa=id&website=" URL_WEBHOOK`
3. Klik **Test trigger**, lalu susun langkahnya seperti automation lama (Find records → Conditional → Create record di tabel **Newsletter Subscribers**, termasuk kolom **Bahasa**).
4. Nyalakan automation, lalu isi secret `NEWSLETTER_WEBHOOK_URL` dengan URL webhook baru.

## Saat domain sendiri sudah dibeli

1. Di GitHub: **Settings → Pages → Custom domain**, isi domain (misalnya `www.domainanda.com`), lalu Save. GitHub membuat file `CNAME` otomatis.
2. Di pengelola domain, arahkan DNS sesuai panduan GitHub Pages: record `CNAME` untuk `www` ke `hi-kreasidigital.github.io`, dan record `A` untuk domain utama ke IP GitHub Pages.
3. Setelah domain aktif, centang **Enforce HTTPS**.
4. Ubah secrets:
   - `SITE_BASE_URL` → `https://www.domainanda.com`
   - `BASE_PATH` → **dikosongkan**
5. Jalankan **Run workflow** sekali. Semua link, canonical, hreflang, dan sitemap otomatis pindah ke domain baru.
6. Di Google Search Console, tambahkan properti **Domain** baru (verifikasi lewat DNS), lalu kirim `https://www.domainanda.com/sitemap.xml`.

## Catatan teknis

- Script: `scripts/generate_from_airtable.py`. Teks bawaan (dipakai kalau sebuah Key di tabel Teks Situs kosong atau terhapus) ada di `scripts/site_text.py`.
- Tampilan: `scripts/assets_src/site.css` dan `site.js`. Script menyalinnya ke `assets/` setiap build.
- Pengalihan URL lama diatur di `LEGACY_REDIRECTS` di dalam script.
- `.generated-files.json` mencatat file buatan script, supaya halaman yang tidak lagi Published bisa dihapus otomatis. Jangan dihapus.
