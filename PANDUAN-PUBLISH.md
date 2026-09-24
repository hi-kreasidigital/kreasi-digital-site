# Panduan Publish Website Kreasi Digital

Urutannya penting — ikuti dari atas ke bawah. Total sekitar 30–45 menit.

Peran tiap layanan:
- **Airtable** — tempat kamu edit semua konten (artikel, studi kasus, teks section, kontak), sekaligus tempat menampung pendaftar newsletter (lewat Airtable Automation)
- **GitHub** — tempat file website disimpan, sekaligus mesin yang build ulang situs otomatis
- **GitHub Pages** — hosting gratis situsnya

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

**Kalau folder `.github/` tidak mau terupload:** di repo, klik **Add file → Create new file**, lalu ketik nama file persis: `.github/workflows/rebuild.yml` (GitHub otomatis bikin foldernya), paste isi file `rebuild.yml` dari zip, lalu commit. (Di macOS, folder berawalan titik disembunyikan Finder — tekan `Cmd+Shift+.` untuk menampilkannya.)

8. **Upload gambar-gambar kamu.** File gambar lama (logo.png, hero-illustration.png, foto portofolio) tidak ada di zip. Upload semuanya ke root repo dengan cara yang sama, pakai nama file yang sama seperti sebelumnya.

---

## TAHAP 2 — Ambil token Airtable

1. Buka https://airtable.com/create/tokens → **Create new token**.
2. **Name**: `kreasi-digital-website`
3. **Scopes**: tambahkan `data.records:read` saja (cukup baca — script tidak perlu menulis ke Airtable).
4. **Access**: pilih base **Kreasi Digital**.
5. Klik **Create token**, lalu **salin tokennya sekarang** (hanya ditampilkan sekali). Simpan sementara di notepad.

Base ID kamu sudah diketahui: `appTgtEPUl5kIRHvv`

**Token ini JANGAN pernah ditaruh di HTML atau file publik mana pun.** Token hanya disimpan sebagai GitHub Secret (Tahap 4) dan dipakai GitHub Actions untuk membaca konten saat build.

---

## TAHAP 3 — Setup newsletter (Airtable Automation + webhook)

Form newsletter di situs mengirim email pendaftar ke **webhook** milik sebuah Airtable Automation. Automation itu lalu menyimpan pendaftar ke tabel **CMS - Newsletter Subscribers**.

> **Sudah pernah disetup?** Automation **"Newsletter: simpan pendaftar dari website"** (ID `wfl1Fy5OOp9d7I8Rz`) sudah ada dan aktif di base `appTgtEPUl5kIRHvv`, dan URL webhook-nya sudah tertanam di `scripts/generate_from_airtable.py`. Tahap ini hanya perlu diulang kalau automation-nya terhapus atau kamu membuat base baru.

**Kenapa URL webhook aman dipajang di HTML publik?** URL itu hanya bisa memicu automation tersebut (menambah pendaftar). URL itu tidak bisa membaca, mengubah, atau menghapus data apa pun di Airtable — berbeda dengan token Airtable, yang tidak boleh dipajang.

**Kenapa tidak langsung menulis ke Airtable dari form?** Itu butuh token Airtable di HTML publik, dan izin token berlaku untuk seluruh base (termasuk tabel CMS) — siapa pun bisa mengubah isi situs.

### Membuat automation dari nol

1. Buka base di Airtable → tab **Automations** → **Create automation**. Beri nama `Newsletter: simpan pendaftar dari website`.
2. **Trigger**: pilih **When webhook received**. Salin **URL webhook** yang muncul.
3. **Kirim data contoh** supaya Airtable tahu bentuk datanya. Buka aplikasi **Terminal** di Mac, lalu jalankan (ganti `URL_WEBHOOK`):
   ```
   curl -X POST -d "email=tes@contoh.com&sumber_halaman=Beranda&website=" URL_WEBHOOK
   ```
   Kembali ke Airtable, klik **Test trigger**. Harus muncul field `email`, `sumber_halaman`, dan `website`.
4. **Action 1 — Find records**: tabel **CMS - Newsletter Subscribers**, kondisi **Email** *is* `email` dari trigger. (Gunanya mengecek email ganda.)
5. **Action 2 — Conditional group** dengan kondisi (semua harus terpenuhi):
   - `website` dari trigger **is empty** (field jebakan bot — pengunjung manusia tidak melihatnya, bot biasanya mengisinya)
   - `email` dari trigger **contains** `@`
   - hasil **Find records** (daftar record ID) **is empty** (email belum terdaftar)
6. Di dalam kondisi itu, tambahkan **Create record** di tabel **CMS - Newsletter Subscribers**:
   - **Email** → `email` dari trigger (idealnya diubah ke huruf kecil & tanpa spasi)
   - **Tanggal Daftar** → waktu automation berjalan
   - **Sumber Halaman** → `sumber_halaman` dari trigger
7. Nyalakan toggle automation menjadi **On**.
8. Jalankan lagi perintah `curl` di langkah 3. Dalam beberapa detik, baris `tes@contoh.com` harus muncul di tabel. Kalau sudah, hapus baris tes itu.
9. **Pasang URL webhook di skrip**: buka `scripts/generate_from_airtable.py`, cari `NEWSLETTER_WEBHOOK_URL`, lalu ganti URL default di situ dengan URL webhook yang baru. Commit.

**Catatan teknis penting (jangan diubah tanpa alasan kuat):** webhook Airtable **tidak mendukung CORS**. Karena itu form di situs mengirim data sebagai **form biasa** (`URLSearchParams`) dengan mode `no-cors`. Kiriman JSON akan diblokir browser, dan kiriman teks biasa (`text/plain`) ditolak Airtable. Konsekuensinya, browser tidak bisa membaca balasan Airtable — pesan "Makasih!" tampil setelah kiriman berangkat, sedangkan cek duplikat dan filter bot dilakukan di automation.

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

Ganti `USERNAME` dengan username GitHub kamu, dan `kreasi-digital` dengan nama repo kamu kalau berbeda.

**`BASE_PATH` itu penting.** Karena URL gratis GitHub Pages berbentuk `username.github.io/nama-repo/`, semua link internal harus diberi awalan nama repo. Tanpa ini, semua menu dan tombol di situs akan mengarah ke halaman 404.

**`SITE_BASE_URL` harus sudah menyertakan nama repo** (contoh `https://USERNAME.github.io/kreasi-digital`, tanpa garis miring di akhir). Nilai ini dipakai langsung untuk canonical URL dan `sitemap.xml`.

**URL webhook newsletter tidak perlu dijadikan secret** — sudah tertulis di skrip (Tahap 3 langkah 9). Secret `NEWSLETTER_WEBHOOK_URL` hanya opsional untuk menimpa nilai itu; kalau dipakai, pastikan `rebuild.yml` juga meneruskannya ke skrip di bagian `env`.

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

Form newsletter tidak perlu diubah saat pindah domain — webhook Airtable menerima kiriman dari domain mana pun.

Setelah itu, daftarkan ulang domain baru di Google Search Console sebagai property terpisah.

---

## Cek hasil & troubleshooting

**Cek newsletter jalan:** buka halaman Beranda atau Blog situsmu, masukkan email uji, klik Daftar. Lalu cek tabel **CMS - Newsletter Subscribers** di Airtable. Emailnya harus muncul dalam beberapa detik, lengkap dengan tanggal dan sumber halaman.

**Pendaftar newsletter tidak masuk ke Airtable?** Cek berurutan:
1. Automation **"Newsletter: simpan pendaftar dari website"** masih **On**.
2. Riwayat run automation (Automations → buka automation → run history). Kalau tidak ada run sama sekali, kiriman tidak sampai ke webhook.
3. Situs sudah memakai form versi terbaru: klik kanan di halaman → **View Page Source** → cari `hooks.airtable.com`. Kalau tidak ketemu, workflow belum jalan ulang setelah skrip diubah, atau browser masih menyimpan versi lama (coba jendela Incognito).
4. Email yang sama didaftarkan dua kali memang sengaja tidak disimpan ulang.

**Semua link 404?** `BASE_PATH` salah atau belum diisi. Nilainya harus `/nama-repo` persis, diawali garis miring, tanpa garis miring di akhir.

**Workflow merah di Actions?** Klik job yang gagal → baca log. Biasanya: token Airtable salah/kadaluarsa, atau nama secret typo.

**Gambar tidak muncul?** File gambar belum diupload ke repo, atau nama filenya beda (huruf besar/kecil berpengaruh di GitHub Pages).

**Konten di Airtable sudah diubah tapi situs belum berubah?** Workflow jalan tiap 15 menit. Untuk artikel dan studi kasus, pastikan kolom **Status** sudah diset ke **Published**.
