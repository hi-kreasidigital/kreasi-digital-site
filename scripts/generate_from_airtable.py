#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-publish generator untuk situs Kreasi Digital.

Cara kerja:
1. Ambil data dari 5 tabel Airtable (Pengaturan Situs, Kontak, Studi Kasus,
   Artikel Blog) lewat REST API Airtable.
2. Bangun ulang halaman statis (index.html, blog.html, studi-kasus-*.html,
   artikel-*.html) dan tempel ulang header/footer/kontak yang konsisten
   di semua halaman lain (termasuk 3 halaman layanan).
3. Simpan hasilnya ke folder repo (root), siap di-commit oleh GitHub Actions.

ENV VARS yang dibutuhkan (diisi sebagai GitHub Actions secrets):
- AIRTABLE_API_KEY  : Personal Access Token Airtable (scope: data.records:read, minimal)
- AIRTABLE_BASE_ID  : ID base, contoh appTgtEPUl5kIRHvv
- SITE_BASE_URL     : domain final situs, contoh https://www.kreasidigital.id

ENV VAR opsional:
- NEWSLETTER_WEBHOOK_URL : URL webhook Airtable Automation untuk form newsletter.
  Kalau tidak diisi, dipakai nilai default di bawah (NEWSLETTER_WEBHOOK_URL).

Script ini TIDAK menghapus halaman yang tidak dikenal -- ia hanya menulis ulang
file-file yang memang jadi tanggung jawabnya (lihat MANAGED_FILES).
"""
import os
import re
import json
import urllib.request
import urllib.parse

AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://www.kreasidigital.id").rstrip("/")
REPO_ROOT = os.environ.get("REPO_ROOT", ".")
# BASE_PATH: kosongkan ("") kalau situs disajikan di root domain.
# Isi "/nama-repo" kalau pakai GitHub Pages project page
# (contoh: username.github.io/nama-repo -> BASE_PATH="/nama-repo")
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")

# Newsletter: form publik mengirim ke webhook Airtable Automation
# "Newsletter: simpan pendaftar dari website", yang lalu menyimpan email ke
# tabel "CMS - Newsletter Subscribers". URL webhook ini memang akan terlihat di
# HTML publik -- itu aman: URL ini HANYA bisa memicu automation tsb (menambah
# pendaftar), tidak bisa membaca/mengubah/menghapus data apa pun di Airtable.
# Kalau webhook diganti (misal automation dibuat ulang), update nilai di bawah
# ATAU isi secret NEWSLETTER_WEBHOOK_URL. Kosongkan untuk menyembunyikan form.
NEWSLETTER_WEBHOOK_URL = os.environ.get(
    "NEWSLETTER_WEBHOOK_URL",
    "https://hooks.airtable.com/workflows/v1/genericWebhook/appTgtEPUl5kIRHvv/wfl1Fy5OOp9d7I8Rz/wtr6q8E91WOTrCTcK",
).strip()


def u(path):
    """Bangun URL internal yang menghormati BASE_PATH."""
    if not path.startswith("/"):
        return path
    return f"{BASE_PATH}{path}"

TABLES = {
    "pengaturan": "CMS - Pengaturan Situs",
    "kontak": "CMS - Kontak",
    "studi_kasus": "CMS - Studi Kasus",
    "artikel": "CMS - Artikel Blog",
    "proses": "CMS - Proses Kerja",
    "faq": "CMS - FAQ Layanan",
    "tim": "CMS - Tim",
    "sosmed": "CMS - Sosial Media",
}

WA_FALLBACK = "https://wa.me/6285117732474"

CSS = """
:root {
    --bg-white: #FFFFFF; --bg-light: #F8FAFC; --primary: #1E293B;
    --yellow-accent: #FEBF23; --pink-btn: #FFD7EF; --text-main: #0F172A;
    --text-muted: #64748B; --border-light: #E2E8F0; --radius-lg: 16px; --radius-md: 12px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.05); --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 25px -5px rgba(0,0,0,0.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: var(--bg-white); color: var(--text-main); line-height: 1.6; overflow-x: hidden; }
.container { max-width: 1140px; margin: 0 auto; padding: 0 24px; }
header { padding: 16px 0; background: rgba(255,255,255,0.98); backdrop-filter: blur(8px); border-bottom: 1px solid var(--border-light); position: sticky; top: 0; z-index: 100; }
.nav-wrapper { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.logo-link { display: flex; align-items: center; text-decoration: none; background: transparent; }
.brand-logo { height: auto; max-height: 60px; width: auto; object-fit: contain; background: transparent; }
.nav-links { display: flex; gap: 20px; list-style: none; align-items: center; flex-wrap: wrap; }
.nav-links a { text-decoration: none; color: var(--text-main); font-weight: 600; font-size: 0.92rem; transition: color 0.2s ease; }
.nav-links a:hover { color: var(--primary); }
.breadcrumb { font-size: 0.85rem; color: var(--text-muted); padding: 14px 0; }
.breadcrumb a { color: var(--text-muted); text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }
.btn-cta, .card-btn, .btn-outline { padding: 12px 28px; border-radius: 30px; font-weight: 700; text-decoration: none; display: inline-block; transition: all 0.2s ease; box-shadow: var(--shadow-sm); border: none; text-align: center; }
.btn-cta, .card-btn { background: var(--pink-btn); color: var(--text-main) !important; }
.btn-outline { background: transparent; color: var(--text-main) !important; border: 2px solid var(--border-light); box-shadow: none; }
.btn-cta:hover, .card-btn:hover, .btn-outline:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); filter: brightness(0.97); }
.cta-row { display: flex; gap: 14px; flex-wrap: wrap; }
.hero { padding: 60px 0; background: linear-gradient(180deg, var(--bg-white) 0%, var(--bg-light) 100%); }
.hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; }
.hero-title { font-size: 2.6rem; font-weight: 800; line-height: 1.2; margin-bottom: 20px; color: var(--primary); }
.hero-title span { background: var(--yellow-accent); padding: 0 6px; border-radius: 4px; color: #000; }
.hero-subtitle { font-size: 1.05rem; color: var(--text-muted); margin-bottom: 32px; }
.hero-illustration-img { width: 100%; height: auto; max-height: 380px; object-fit: contain; }
.banner-accent { background: var(--bg-light); border-top: 1px solid var(--border-light); border-bottom: 1px solid var(--border-light); padding: 40px 0; }
.banner-content { text-align: center; max-width: 840px; margin: 0 auto; color: var(--primary); }
.banner-content h3 { font-size: 1.5rem; font-weight: 800; margin-bottom: 8px; }
.banner-content p { font-size: 1.1rem; font-weight: 500; font-style: italic; }
section { padding: 60px 0; }
.section-header { text-align: center; margin-bottom: 40px; }
.section-tag { display: inline-block; background: var(--yellow-accent); color: #000; padding: 6px 18px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; margin-bottom: 12px; letter-spacing: 0.5px; text-transform: uppercase; }
.section-title { font-size: 2.1rem; font-weight: 800; color: var(--text-main); }
.story-card { background: var(--bg-white); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 40px; box-shadow: var(--shadow-md); }
.team-box { display: flex; gap: 20px; margin-top: 24px; flex-wrap: wrap; }
.team-member { flex: 1; min-width: 160px; background: var(--bg-light); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 20px; text-align: center; }
.member-avatar { width: 90px; height: 90px; border-radius: 50%; margin: 0 auto 12px; overflow: hidden; box-shadow: var(--shadow-sm); }
.member-avatar img { width: 100%; height: 100%; object-fit: cover; }
.member-name { font-weight: 700; color: var(--primary); }
.member-role { font-size: 0.85rem; color: var(--text-muted); }
.portfolio-grid, .service-grid, .article-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 28px; }
.portfolio-card, .service-card, .article-card { background: var(--bg-white); border: 1px solid var(--border-light); border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-sm); transition: transform 0.2s ease, box-shadow 0.2s ease; display: flex; flex-direction: column; }
.portfolio-card:hover, .service-card:hover, .article-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.card-img-container { height: 180px; background: var(--bg-light); overflow: hidden; }
.card-img-container img { width: 100%; height: 100%; object-fit: cover; object-position: top; }
.card-body { padding: 24px; display: flex; flex-direction: column; flex-grow: 1; }
.card-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 8px; color: var(--primary); }
.card-desc { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 20px; flex-grow: 1; }
.card-btn { width: 100%; }
.app-illustration-container { text-align: center; margin: 0 auto 40px auto; max-width: 450px; }
.app-illustration-container img { width: 100%; height: auto; object-fit: contain; }
.article-body { max-width: 760px; margin: 0 auto; }
.article-body h2 { font-size: 1.5rem; font-weight: 800; color: var(--primary); margin: 32px 0 12px; }
.article-body p { color: var(--text-muted); margin-bottom: 14px; }
.article-body ul, .article-body ol { color: var(--text-muted); margin: 0 0 14px 22px; }
.article-body li { margin-bottom: 6px; }
.article-meta { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 24px; }
.result-box { background: var(--bg-light); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 24px; margin: 24px 0; }
.result-box h4 { color: var(--primary); margin-bottom: 10px; }
.callout { background: var(--bg-light); border-left: 4px solid var(--yellow-accent); border-radius: var(--radius-md); padding: 18px 22px; margin: 22px 0; color: var(--text-main); }
.faq-item { border-bottom: 1px solid var(--border-light); padding: 18px 0; }
.faq-item h4 { color: var(--primary); margin-bottom: 8px; font-size: 1.02rem; }
.process-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin: 24px 0; }
.process-step { background: var(--bg-white); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 20px; box-shadow: var(--shadow-sm); }
.process-step .step-num { display: inline-block; background: var(--primary); color: #fff; width: 30px; height: 30px; border-radius: 50%; text-align: center; line-height: 30px; font-weight: 700; margin-bottom: 10px; }
.process-step h4 { color: var(--primary); margin-bottom: 6px; }
.process-step p { color: var(--text-muted); font-size: 0.92rem; margin: 0; }
footer { background: var(--yellow-accent); color: #000; padding: 50px 0 30px; border-top: 1px solid var(--border-light); }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 40px; margin-bottom: 30px; }
.footer-logo { height: auto; max-height: 60px; width: auto; margin-bottom: 16px; object-fit: contain; background: transparent; }
.footer-bottom { border-top: 1px solid rgba(0,0,0,0.15); padding-top: 20px; text-align: center; font-size: 0.9rem; color: #000; }
.footer-bottom a { color: #000; font-weight: 700; text-decoration: underline; }
.footer-subtext { display: block; margin-top: 4px; font-size: 0.85rem; font-weight: 600; }
footer h4 { font-weight: 700; margin-bottom: 16px; color: #000; }
footer a.footlink { color: #000; text-decoration: none; display:block; margin-bottom: 8px; font-weight: 600; font-size: 0.9rem;}
footer a.footlink:hover { text-decoration: underline; }
.sosmed-row { display: flex; gap: 12px; flex-wrap: wrap; }
.sosmed-icon { width: 38px; height: 38px; border-radius: 50%; overflow: hidden; background: #fff; display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-sm); }
.sosmed-icon img { width: 100%; height: 100%; object-fit: cover; }
.whatsapp-float { position: fixed; width: 60px; height: 60px; bottom: 30px; right: 30px; background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center; font-size: 30px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2); z-index: 999; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; }
.whatsapp-float:hover { transform: scale(1.1); background-color: #128c7e; }
.whatsapp-icon { width: 34px; height: 34px; fill: white; }
.nl-trap { position: absolute; left: -10000px; top: auto; width: 1px; height: 1px; overflow: hidden; }
@media (max-width: 768px) {
    .nav-wrapper { flex-direction: column; gap: 16px; }
    .nav-links { width: 100%; justify-content: center; flex-wrap: wrap; gap: 12px; }
    .hero-grid, .story-grid, .footer-grid { grid-template-columns: 1fr; gap: 32px; }
    .hero-title { font-size: 2rem; }
    .whatsapp-float { width: 50px; height: 50px; bottom: 20px; right: 20px; }
}
"""


def airtable_get(table_name, filter_formula=None):
    """Fetch all records from a table, handling pagination."""
    records = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if filter_formula:
            params["filterByFormula"] = filter_formula
        if offset:
            params["offset"] = offset
        url = f"https://api.airtable.com/v0/{BASE_ID}/{urllib.parse.quote(table_name)}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def field(rec, name, default=""):
    return rec.get("fields", {}).get(name, default)


def attachment_url(rec, field_name, fallback):
    atts = field(rec, field_name, [])
    if atts and isinstance(atts, list) and atts[0].get("url"):
        return atts[0]["url"]
    return fallback


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def md_to_html(text):
    """Very small markdown-ish converter: blank line = new paragraph, '## ' = h2."""
    blocks = re.split(r"\n\s*\n", text.strip())
    html = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b.startswith("## "):
            html.append(f"<h2>{esc(b[3:])}</h2>")
        else:
            html.append(f"<p>{esc(b)}</p>")
    return "\n".join(html)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
pengaturan_rows = {field(r, "Section Key"): r for r in airtable_get(TABLES["pengaturan"])}
kontak_rows = airtable_get(TABLES["kontak"])
kontak = kontak_rows[0] if kontak_rows else {"fields": {}}
studi_kasus_rows = [r for r in airtable_get(TABLES["studi_kasus"]) if field(r, "Status") == "Published"]
artikel_rows = [r for r in airtable_get(TABLES["artikel"]) if field(r, "Status") == "Published"]
proses_rows = airtable_get(TABLES["proses"])
faq_rows = airtable_get(TABLES["faq"])
tim_rows = sorted(airtable_get(TABLES["tim"]), key=lambda r: field(r, "Urutan", 9999) or 9999)
sosmed_rows = sorted(airtable_get(TABLES["sosmed"]), key=lambda r: field(r, "Urutan", 9999) or 9999)

# Foto tim asli yang sudah diupload ke repo, dipetakan dari Nama.
# Dipakai HANYA kalau kolom "Foto" di Airtable kosong.
FALLBACK_TEAM_PHOTO = {
    "Tara": "tara.jpeg",
    "Mattel": "mattel.jpeg",
}


def rows_for_page(rows, halaman_name):
    filtered = [r for r in rows if field(r, "Halaman") == halaman_name]
    filtered.sort(key=lambda r: field(r, "Urutan", 9999) or 9999)
    return filtered

# Nama file gambar asli yang sudah kamu upload ke repo, dipetakan dari slug
# studi kasus. Dipakai HANYA kalau kolom "Gambar Cover" di Airtable kosong.
# Kalau kamu tambah studi kasus baru: upload fotonya lewat kolom "Gambar
# Cover" di Airtable (paling gampang), ATAU tambahkan baris baru di sini.
FALLBACK_COVER_BY_SLUG = {
    "studi-kasus-tattoo-in-bali": "tattoo-in-bali.jpg",
    "studi-kasus-pride-on": "pride-on.jpg",
    "studi-kasus-bali-island-driver": "bali-island-driver.jpg",
    "studi-kasus-aussie-souvenirs": "aussie-souvenirs.jpg",
    "studi-kasus-nota-pos": "nota-pos.jpg",
    "studi-kasus-outreach-cafe-malang": "outreach-cafe.jpg",
    "studi-kasus-rekap-warga": "rekap-warga.jpg",
}


def cover_for(rec, slug, title):
    """Prioritas: 1) attachment di Airtable, 2) file asli yang sudah diupload
    ke repo, 3) placeholder otomatis (kalau dua-duanya tidak ada)."""
    atts = field(rec, "Gambar Cover", [])
    if atts and isinstance(atts, list) and atts[0].get("url"):
        return atts[0]["url"]
    if slug in FALLBACK_COVER_BY_SLUG:
        return u("/" + FALLBACK_COVER_BY_SLUG[slug])
    return f"https://placehold.co/600x400/F8FAFC/1E293B?text={urllib.parse.quote(title)}"

WA_LINK = f"https://wa.me/{re.sub(r'[^0-9]', '', field(kontak, 'Nomor WhatsApp', '6285117732474'))}"
EMAIL = field(kontak, "Email", "hi.kreasi.digital@gmail.com")
NAMA_BISNIS = field(kontak, "Nama Bisnis", "Kreasi Digital")

header_row = pengaturan_rows.get("header", {"fields": {}})
footer_row = pengaturan_rows.get("footer", {"fields": {}})

LOGO_URL = attachment_url(header_row, "Gambar", u("/logo.png"))
NAV_WA_TEXT = field(header_row, "Teks Tombol", "Chat via WhatsApp")

WHATSAPP_SVG = """<svg class="whatsapp-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3 18.6-68.1-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-32.6-16.3-54-29.1-75.5-66-5.7-9.8 5.7-9.1 16.3-30.3 1.8-3.7.9-6.9-.5-9.7-1.4-2.8-12.5-30.1-17.1-41.2-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 35.2 15.2 49 16.5 66.6 13.9 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>"""

NAV = f"""<header>
    <div class="container nav-wrapper">
        <a href="{u('/index.html')}" class="logo-link">
            <img src="{LOGO_URL}" alt="Logo {esc(NAMA_BISNIS)}" class="brand-logo">
        </a>
        <ul class="nav-links">
            <li><a href="{u('/jasa-website-bali.html')}">Jasa Website</a></li>
            <li><a href="{u('/jasa-kasir-digital-malang.html')}">Kasir Digital (POS)</a></li>
            <li><a href="{u('/dashboard-sistem-umkm.html')}">Dashboard Sistem</a></li>
            <li><a href="{u('/blog.html')}">Blog</a></li>
            <li><a href="{u('/index.html#tentang')}">Tentang</a></li>
            <li><a href="{WA_LINK}" target="_blank" rel="noopener noreferrer" class="btn-cta">{esc(NAV_WA_TEXT)}</a></li>
        </ul>
    </div>
</header>"""

WHATSAPP_FLOAT = f"""<a href="{WA_LINK}" class="whatsapp-float" target="_blank" rel="noopener noreferrer" aria-label="Chat via WhatsApp">{WHATSAPP_SVG}</a>"""

FOOTER_LOGO_URL = attachment_url(footer_row, "Gambar", u("/logo.png"))
FOOTER_TEXT = field(footer_row, "Paragraf / Deskripsi", "Yuk ngobrol! Kita siap jadi teman diskusi dan mitra digital kamu.")

sosmed_html = ""
if sosmed_rows:
    icons = []
    for s in sosmed_rows:
        platform = field(s, "Platform")
        link = field(s, "Link")
        if not link:
            continue
        atts = field(s, "Logo", [])
        logo = atts[0]["url"] if atts and isinstance(atts, list) and atts[0].get("url") else "https://placehold.co/40x40/1E293B/FFFFFF?text=%E2%80%A2"
        icons.append(f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="sosmed-icon" title="{esc(platform)}"><img src="{logo}" alt="{esc(platform)}"></a>')
    if icons:
        sosmed_html = f'<div class="sosmed-row">{"".join(icons)}</div>'
    else:
        sosmed_html = '<p style="font-size:0.85rem;color:#000;">Link sosial media akan segera hadir.</p>'
else:
    sosmed_html = '<p style="font-size:0.85rem;color:#000;">Link sosial media akan segera hadir.</p>'

FOOTER = f"""<footer id="kontak">
    <div class="container">
        <div class="footer-grid">
            <div>
                <img src="{FOOTER_LOGO_URL}" alt="Logo {esc(NAMA_BISNIS)}" class="footer-logo">
                <p style="max-width: 480px; color: #000; font-size: 0.95rem; font-weight: 500;">{esc(FOOTER_TEXT)}</p>
                <p style="margin-top:10px; font-size:0.85rem; color:#000; font-weight:600;">Email: {esc(EMAIL)}</p>
            </div>
            <div>
                <h4>Layanan</h4>
                <a class="footlink" href="{u('/jasa-website-bali.html')}">Jasa Website Bali</a>
                <a class="footlink" href="{u('/jasa-kasir-digital-malang.html')}">Kasir Digital Malang</a>
                <a class="footlink" href="{u('/dashboard-sistem-umkm.html')}">Dashboard Sistem</a>
                <a class="footlink" href="{u('/blog.html')}">Blog Edukasi UMKM</a>
            </div>
            <div>
                <h4>Ikuti Kami</h4>
                {sosmed_html}
            </div>
        </div>
        <div class="footer-bottom">
            <a href="{u('/index.html')}">&copy; 2026 {esc(NAMA_BISNIS)}</a>
            <span class="footer-subtext">Built with care for hardworking entrepreneurs.</span>
        </div>
    </div>
</footer>"""



def newsletter_form(sumber_halaman):
    """Form newsletter yang mengirim ke webhook Airtable Automation.

    Catatan teknis:
    - Dikirim sebagai form biasa (URLSearchParams) dengan mode 'no-cors'.
      Webhook Airtable tidak mendukung CORS, jadi kiriman JSON diblokir browser;
      format form biasa lolos tanpa preflight.
    - Konsekuensi 'no-cors': browser tidak bisa membaca balasan Airtable, jadi
      pesan sukses ditampilkan setelah kiriman berangkat. Cek duplikat, validasi
      email, dan filter bot dilakukan di automation Airtable.
    - Field 'website' adalah jebakan bot (disembunyikan dari pengunjung).
      Kalau terisi, automation tidak menyimpan pendaftar.
    Kalau NEWSLETTER_WEBHOOK_URL kosong, form tidak dirender sama sekali.
    """
    if not NEWSLETTER_WEBHOOK_URL:
        return ""
    return f"""<section style="background:var(--bg-light);">
  <div class="container" style="max-width:640px;text-align:center;">
    <span class="section-tag">Newsletter</span>
    <h2 class="section-title" style="font-size:1.6rem;margin-bottom:10px;">Dapat Tips Digitalisasi UMKM</h2>
    <p style="color:var(--text-muted);margin-bottom:20px;">Kami kirim artikel dan tips praktis sesekali saja. Tanpa spam.</p>
    <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;">
      <input id="nl-email" type="email" placeholder="email@kamu.com" required autocomplete="email"
        style="flex:1;min-width:240px;padding:12px 18px;border-radius:30px;border:1px solid var(--border-light);font-family:inherit;font-size:1rem;">
      <div class="nl-trap" aria-hidden="true">
        <label for="nl-website">Jangan diisi</label>
        <input id="nl-website" type="text" name="website" tabindex="-1" autocomplete="off">
      </div>
      <button id="nl-btn" type="button" class="btn-cta" style="cursor:pointer;">Daftar</button>
    </div>
    <p id="nl-msg" style="margin-top:12px;font-size:0.9rem;color:var(--text-muted);"></p>
  </div>
  <script>
  (function() {{
    var WEBHOOK = '{NEWSLETTER_WEBHOOK_URL}';
    var btn = document.getElementById('nl-btn');
    var input = document.getElementById('nl-email');
    var trap = document.getElementById('nl-website');
    var msg = document.getElementById('nl-msg');
    function daftar() {{
      var email = (input.value || '').trim();
      if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) {{
        msg.textContent = 'Masukkan email yang valid ya.';
        return;
      }}
      btn.disabled = true;
      msg.textContent = 'Mendaftarkan...';
      fetch(WEBHOOK, {{
        method: 'POST',
        mode: 'no-cors',
        body: new URLSearchParams({{
          email: email,
          sumber_halaman: '{sumber_halaman}',
          website: trap.value || ''
        }})
      }}).then(function() {{
        msg.textContent = 'Makasih! Email kamu sudah kami catat.';
        input.value = '';
        btn.disabled = false;
      }}).catch(function() {{
        msg.textContent = 'Maaf, ada kendala koneksi. Coba lagi nanti ya.';
        btn.disabled = false;
      }});
    }}
    btn.addEventListener('click', daftar);
    input.addEventListener('keydown', function(e) {{
      if (e.key === 'Enter') {{ e.preventDefault(); daftar(); }}
    }});
  }})();
  </script>
</section>"""


def write_file(rel_path, content):
    full = os.path.join(REPO_ROOT, rel_path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", rel_path)


def page_shell(slug, title, description, body_html, schema=None, breadcrumb=None):
    canonical = f"{SITE_BASE_URL}/{slug}"
    bc_html = ""
    if breadcrumb:
        parts = [f'<a href="{u(href)}">{name}</a>' if href else f"<span>{name}</span>" for name, href in breadcrumb]
        bc_html = '<div class="container breadcrumb">' + " &rsaquo; ".join(parts) + "</div>"
    schema_html = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="google-site-verification" content="Zm8rUHDS_EffoluHuIbreulEjK4y8wek20QiN7TyTIE" />
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
{schema_html}
</head>
<body>
{NAV}
{bc_html}
{body_html}
{FOOTER}
{WHATSAPP_FLOAT}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Studi Kasus pages
# ---------------------------------------------------------------------------
studi_kasus_cards = []
for r in studi_kasus_rows:
    slug = field(r, "Slug URL")
    title = field(r, "Judul Proyek")
    ringkasan = field(r, "Ringkasan (Meta Description)")
    tantangan = field(r, "Tantangan Klien")
    solusi = field(r, "Solusi Kreasi Digital")
    hasil_lines = [l for l in field(r, "Hasil / Dampak").split("\n") if l.strip()]
    link_asli = field(r, "Link Website Asli")
    cover = cover_for(r, slug, title)

    body = f"""<section style="padding-top:20px;">
  <div class="container article-body">
    <span class="section-tag">Studi Kasus</span>
    <h1 style="font-size:2rem;font-weight:800;color:var(--primary);margin:14px 0 6px;">Studi Kasus: {esc(title)}</h1>
    <p class="article-meta">{esc(NAMA_BISNIS)} &middot; Studi Kasus Klien</p>
    <div class="card-img-container" style="height:300px;border-radius:var(--radius-lg);margin-bottom:24px;">
      <img src="{cover}" alt="Tampilan {esc(title)}" style="width:100%;height:100%;object-fit:cover;">
    </div>
    <h2>Tantangan</h2>
    <p>{esc(tantangan)}</p>
    <h2>Solusi dari {esc(NAMA_BISNIS)}</h2>
    <p>{esc(solusi)}</p>
    <div class="result-box">
      <h4>Hasil</h4>
      <ul>{''.join(f'<li>{esc(l)}</li>' for l in hasil_lines)}</ul>
    </div>
    {"<h2>Lihat Langsung</h2><p>Kamu bisa cek langsung hasil kerja kami di link berikut (akan membuka situs pihak klien di tab baru):</p><div class='cta-row'><a href='" + link_asli + "' target='_blank' rel='noopener noreferrer nofollow' class='btn-outline'>Kunjungi Website " + esc(title) + " &#8599;</a><a href='" + WA_LINK + "' target='_blank' rel='noopener noreferrer' class='btn-cta'>Mau Punya yang Serupa? Chat Kami</a></div>" if link_asli else ""}
  </div>
</section>"""

    schema = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": f"Studi Kasus: {title}", "description": ringkasan,
        "author": {"@type": "Organization", "name": NAMA_BISNIS},
        "publisher": {"@type": "Organization", "name": NAMA_BISNIS},
        "mainEntityOfPage": f"{SITE_BASE_URL}/{slug}.html",
    }
    write_file(f"{slug}.html", page_shell(
        f"{slug}.html", f"Studi Kasus: {title} | {NAMA_BISNIS}", ringkasan, body, schema,
        breadcrumb=[("Beranda", "/index.html"), ("Blog", "/blog.html"), (title, None)],
    ))
    studi_kasus_cards.append((title, ringkasan, cover, f"/{slug}.html"))

# ---------------------------------------------------------------------------
# Artikel Blog pages
# ---------------------------------------------------------------------------
artikel_cards = []
for r in artikel_rows:
    slug = field(r, "Slug URL")
    title = field(r, "Judul Artikel")
    ringkasan = field(r, "Ringkasan (Meta Description)")
    isi = field(r, "Isi Artikel")
    cover = cover_for(r, slug, title)

    body = f"""<section style="padding-top:20px;">
  <div class="container article-body">
    <span class="section-tag">Edukasi UMKM</span>
    <h1 style="font-size:2rem;font-weight:800;color:var(--primary);margin:14px 0 6px;">{esc(title)}</h1>
    <p class="article-meta">{esc(NAMA_BISNIS)} &middot; Artikel Edukasi</p>
    {md_to_html(isi)}
    <div class="cta-row" style="margin-top:24px;">
      <a href="{WA_LINK}" target="_blank" rel="noopener noreferrer" class="btn-cta">Konsultasi Gratis</a>
      <a href="{u('/blog.html')}" class="btn-outline">Baca Artikel Lain &rarr;</a>
    </div>
  </div>
</section>"""

    schema = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": ringkasan,
        "author": {"@type": "Organization", "name": NAMA_BISNIS},
        "publisher": {"@type": "Organization", "name": NAMA_BISNIS},
        "mainEntityOfPage": f"{SITE_BASE_URL}/{slug}.html",
    }
    write_file(f"{slug}.html", page_shell(
        f"{slug}.html", f"{title} | {NAMA_BISNIS}", ringkasan, body, schema,
        breadcrumb=[("Beranda", "/index.html"), ("Blog", "/blog.html"), (title, None)],
    ))
    artikel_cards.append((title, ringkasan, cover, f"/{slug}.html"))

# ---------------------------------------------------------------------------
# Blog index (list semua artikel + studi kasus)
# ---------------------------------------------------------------------------
def render_cards(cards, cta_label):
    out = []
    for title, desc, img, href in cards:
        out.append(f"""<div class="article-card">
  <div class="card-img-container"><img src="{img}" alt="{esc(title)}"></div>
  <div class="card-body">
    <h3 class="card-title">{esc(title)}</h3>
    <p class="card-desc">{esc(desc)}</p>
    <a href="{u(href)}" class="card-btn">{cta_label}</a>
  </div>
</div>""")
    return "\n".join(out)

blog_body = f"""<section class="hero" style="padding-bottom:20px;">
  <div class="container">
    <div class="section-header" style="text-align:left;">
      <span class="section-tag">Blog {esc(NAMA_BISNIS)}</span>
      <h1 class="hero-title" style="font-size:2.2rem;">Studi Kasus & Edukasi UMKM</h1>
      <p class="hero-subtitle">Cerita proyek yang sudah kami kerjakan, dan tips seputar digitalisasi usaha untuk UMKM di Bali, Malang, dan sekitarnya.</p>
    </div>
  </div>
</section>
<section style="padding-top:0;">
  <div class="container">
    <h2 style="margin-bottom:20px;">Studi Kasus</h2>
    <div class="article-grid" style="margin-bottom:48px;">{render_cards(studi_kasus_cards, "Baca Studi Kasus &rarr;")}</div>
    <h2 style="margin-bottom:20px;">Artikel Edukasi UMKM</h2>
    <div class="article-grid">{render_cards(artikel_cards, "Baca Artikel &rarr;")}</div>
  </div>
</section>
""" + newsletter_form("Blog")

write_file("blog.html", page_shell(
    "blog.html", f"Blog {NAMA_BISNIS} | Edukasi Digitalisasi UMKM",
    f"Blog {NAMA_BISNIS} berisi studi kasus proyek dan artikel edukasi seputar jasa website, kasir digital, dan tips digitalisasi UMKM di Bali, Malang, dan seluruh Indonesia.",
    blog_body,
))

# ---------------------------------------------------------------------------
# Index / Beranda -- hanya bagian yang datanya ada di Pengaturan Situs
# ---------------------------------------------------------------------------
hero = pengaturan_rows.get("hero-beranda", {"fields": {}})
banner = pengaturan_rows.get("banner-quote", {"fields": {}})
tentang = pengaturan_rows.get("tentang-kami", {"fields": {}})

team_html = ""
if tim_rows:
    members = []
    for t in tim_rows:
        nama = field(t, "Nama")
        peran = field(t, "Jabatan")
        atts = field(t, "Foto", [])
        if atts and isinstance(atts, list) and atts[0].get("url"):
            foto = atts[0]["url"]
        elif nama in FALLBACK_TEAM_PHOTO:
            foto = u("/" + FALLBACK_TEAM_PHOTO[nama])
        else:
            foto = f"https://placehold.co/200x200/F8FAFC/1E293B?text={urllib.parse.quote(nama)}"
        members.append(f"""<div class="team-member">
  <div class="member-avatar"><img src="{foto}" alt="Foto {esc(nama)}"></div>
  <div class="member-name">{esc(nama)}</div>
  <div class="member-role">{esc(peran)}</div>
</div>""")
    team_html = f'<div class="team-box">{"".join(members)}</div>'

index_body = f"""<section class="hero">
  <div class="container hero-grid">
    <div>
      <h1 class="hero-title">{esc(field(hero, 'Judul'))}</h1>
      <p class="hero-subtitle">{esc(field(hero, 'Paragraf / Deskripsi'))}</p>
      <div class="cta-row">
        <a href="{field(hero, 'Link Tombol') or WA_LINK}" target="_blank" rel="noopener noreferrer" class="btn-cta">{esc(field(hero, 'Teks Tombol', 'Curhatin Kebutuhan Usaha Kamu'))}</a>
        <a href="{u('/blog.html')}" class="btn-outline">Baca Tips UMKM</a>
      </div>
    </div>
    <div><img src="{u('/hero-illustration.png')}" alt="Ilustrasi {esc(NAMA_BISNIS)}" class="hero-illustration-img"></div>
  </div>
</section>
<div class="banner-accent">
  <div class="container banner-content">
    <h3>{esc(field(banner, 'Judul'))}</h3>
    <p>&ldquo;{esc(field(banner, 'Paragraf / Deskripsi'))}&rdquo;</p>
  </div>
</div>
<section id="tentang">
  <div class="container">
    <div class="section-header"><span class="section-tag">Tentang {esc(NAMA_BISNIS)}</span>
      <h2 class="section-title">{esc(field(tentang, 'Judul'))}</h2></div>
    <div class="story-card"><p style="color:var(--text-muted);">{esc(field(tentang, 'Paragraf / Deskripsi'))}</p>{team_html}</div>
  </div>
</section>
<section style="background:var(--bg-light);">
  <div class="container">
    <div class="section-header"><span class="section-tag">Portofolio</span><h2 class="section-title">Studi Kasus Terbaru</h2></div>
    <div class="portfolio-grid">{render_cards(studi_kasus_cards[:6], "Baca Studi Kasus &rarr;")}</div>
  </div>
</section>
""" + newsletter_form("Beranda")

write_file("index.html", page_shell(
    "index.html", f"{NAMA_BISNIS} | Jasa Website, Kasir Digital & Dashboard untuk UMKM Bali & Malang",
    "Kreasi Digital adalah jasa pembuatan website, aplikasi kasir digital (POS), dan dashboard sistem custom untuk UMKM di Bali & Malang.",
    index_body,
))

# ---------------------------------------------------------------------------
# 3 Halaman Layanan -- hero, proses kerja & FAQ full dari Airtable;
# studi kasus terkait ditarik otomatis lewat filter Kategori.
# Intro/fitur/callout tetap statis di sini karena tidak diminta dinamis.
# ---------------------------------------------------------------------------
LAYANAN_CONFIG = [
    {
        "slug": "jasa-website-bali",
        "hero_key": "hero-layanan-website",
        "halaman": "Layanan Website",
        "kategori": "Website",
        "section_tag": "Layanan Website",
        "intro_title": "Kenapa Pilih Jasa Pembuatan Website di Kreasi Digital?",
        "intro_body": "Kami paham karakter usaha pariwisata dan kreatif di Bali: pelanggan sering datang dari luar negeri, butuh tampilan yang meyakinkan, dan proses pemesanan yang simpel lewat WhatsApp atau form online. Setiap website yang kami buat dirancang mobile-friendly, ringan diakses, dan gampang di-update sendiri.",
        "fitur": [
            "Desain custom sesuai brand usaha kamu, bukan template pasaran",
            "Struktur halaman yang jelas: profil usaha, katalog/layanan, galeri, kontak",
            "Tombol pemesanan langsung ke WhatsApp Business",
            "Optimasi dasar SEO lokal supaya lebih mudah ditemukan di Google saat orang cari \"jasa website Bali\"",
            "Tampilan responsif di HP, tablet, maupun desktop",
        ],
        "callout": "Cocok untuk: villa &amp; homestay, jasa tour &amp; guide, studio tato, toko souvenir, katering, dan usaha jasa lain yang butuh kehadiran online profesional.",
        "meta_description": "Jasa website Bali untuk usaha pariwisata dan kreatif: villa, tour & guide, studio tato, souvenir. Desain custom, mobile-friendly, dan SEO lokal. Konsultasi gratis.",
        "next_page": ("/jasa-kasir-digital-malang.html", "Lihat Jasa Kasir Digital &rarr;"),
    },
    {
        "slug": "jasa-kasir-digital-malang",
        "hero_key": "hero-layanan-pos",
        "halaman": "Layanan Kasir Digital",
        "kategori": "Kasir Digital (POS)",
        "section_tag": "Layanan Kasir Digital",
        "intro_title": "Kenapa Usaha Kamu Butuh Kasir Digital?",
        "intro_body": "Banyak cafe, resto, dan toko kelontong di Malang masih mengandalkan nota kertas atau buku catatan. Selain rawan hilang dan sulit direkap, cara ini bikin pemilik usaha susah tahu produk mana yang paling laku. Dengan sistem kasir digital (POS), semua transaksi tercatat otomatis dan bisa dilihat kapan saja.",
        "fitur": [
            "Pencatatan transaksi harian yang cepat dan minim human error",
            "Rekap penjualan harian, mingguan, dan bulanan otomatis",
            "Laporan produk terlaris untuk bantu keputusan bisnis",
            "Tampilan sederhana, mudah dipelajari kasir baru",
        ],
        "callout": "Cocok untuk: cafe, resto, toko kelontong, dan UMKM kuliner lain di Malang dan sekitarnya yang ingin operasional lebih rapi.",
        "meta_description": "Jasa kasir digital Malang (POS) untuk cafe, resto, dan toko: rekap otomatis, minim human error, mudah dipelajari kasir baru. Konsultasi gratis via WhatsApp.",
        "next_page": ("/dashboard-sistem-umkm.html", "Lihat Layanan Dashboard &rarr;"),
    },
    {
        "slug": "dashboard-sistem-umkm",
        "hero_key": "hero-layanan-dashboard",
        "halaman": "Layanan Dashboard",
        "kategori": "Dashboard",
        "section_tag": "Layanan Dashboard",
        "intro_title": "Untuk Siapa Layanan Ini?",
        "intro_body": "Dashboard sistem cocok untuk usaha atau instansi yang punya banyak data berulang: transaksi, keanggotaan, data warga, inventaris, atau laporan performa. Kami bantu ubah data yang tadinya tersebar di banyak file jadi satu dashboard yang gampang dibaca dan diakses tim kamu.",
        "fitur": [
            "Struktur data sesuai kebutuhan spesifik usaha/instansi kamu",
            "Tampilan rekap & visualisasi data yang mudah dipahami",
            "Akses berbasis web, bisa dibuka dari HP atau laptop",
            "Sistem pencarian dan filter data cepat",
        ],
        "callout": "Cocok untuk: kelurahan/desa (data kependudukan), UMKM dengan banyak cabang, komunitas dengan data keanggotaan, dan usaha yang butuh laporan operasional rutin.",
        "meta_description": "Dashboard sistem custom untuk UMKM dan instansi: rekap data warga, inventaris, atau laporan usaha jadi satu tempat yang mudah diakses tim. Konsultasi gratis.",
        "next_page": ("/jasa-website-bali.html", "Lihat Jasa Website &rarr;"),
    },
]

for cfg in LAYANAN_CONFIG:
    hero = pengaturan_rows.get(cfg["hero_key"], {"fields": {}})
    hero_title = field(hero, "Judul", cfg["intro_title"])
    hero_sub = field(hero, "Paragraf / Deskripsi", "")
    hero_btn = field(hero, "Teks Tombol", "Konsultasi Gratis via WhatsApp")
    hero_link = field(hero, "Link Tombol") or WA_LINK

    proses_steps = rows_for_page(proses_rows, cfg["halaman"])
    proses_html = "\n".join(
        f"""<div class="process-step"><span class="step-num">{i+1}</span>
<h4>{esc(field(p, 'Judul Langkah'))}</h4>
<p>{esc(field(p, 'Deskripsi Langkah'))}</p></div>"""
        for i, p in enumerate(proses_steps)
    )

    faqs = rows_for_page(faq_rows, cfg["halaman"])
    faq_html = "\n".join(
        f"""<div class="faq-item"><h4>{esc(field(f, 'Pertanyaan'))}</h4><p>{esc(field(f, 'Jawaban'))}</p></div>"""
        for f in faqs
    )

    related_cases = [c for r, c in zip(studi_kasus_rows, studi_kasus_cards) if field(r, "Kategori") == cfg["kategori"]][:3]
    related_html = render_cards(related_cases, "Baca Studi Kasus &rarr;") if related_cases else "<p style='color:var(--text-muted);'>Studi kasus untuk kategori ini akan segera hadir.</p>"

    fitur_html = "\n".join(f"<li>{esc(x)}</li>" for x in cfg["fitur"])

    next_href, next_label = cfg["next_page"]

    body = f"""<section class="hero" style="padding-bottom:0;">
  <div class="container">
    <div class="section-header" style="text-align:left; max-width:760px; margin:0 0 24px;">
      <span class="section-tag">{esc(cfg['section_tag'])}</span>
      <h1 class="hero-title" style="font-size:2.2rem;">{esc(hero_title)}</h1>
      <p class="hero-subtitle">{esc(hero_sub)}</p>
      <div class="cta-row"><a href="{hero_link}" target="_blank" rel="noopener noreferrer" class="btn-cta">{esc(hero_btn)}</a></div>
    </div>
  </div>
</section>
<section style="padding-top:0;">
  <div class="container article-body" style="max-width:900px;">
    <h2>{esc(cfg['intro_title'])}</h2>
    <p>{esc(cfg['intro_body'])}</p>
    <h3>Yang Kamu Dapatkan</h3>
    <ul>{fitur_html}</ul>
    <div class="callout">{cfg['callout']}</div>

    <h2>Proses Kerja Kami</h2>
    <div class="process-grid">{proses_html}</div>

    <h2>Studi Kasus Terkait</h2>
    <div class="portfolio-grid">{related_html}</div>

    {"<h2>Pertanyaan yang Sering Ditanyakan</h2>" + faq_html if faqs else ""}

    <div class="cta-row" style="margin-top:28px;">
      <a href="{WA_LINK}" target="_blank" rel="noopener noreferrer" class="btn-cta">Diskusikan Kebutuhan Kamu</a>
      <a href="{u(next_href)}" class="btn-outline">{next_label}</a>
    </div>
  </div>
</section>"""

    schema = {
        "@context": "https://schema.org", "@type": "Service",
        "serviceType": cfg["section_tag"], "provider": {"@type": "ProfessionalService", "name": NAMA_BISNIS},
        "areaServed": ["Bali", "Malang"], "description": cfg["meta_description"],
    }
    if faqs:
        schema = {
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": field(f, "Pertanyaan"),
                 "acceptedAnswer": {"@type": "Answer", "text": field(f, "Jawaban")}}
                for f in faqs
            ],
        }

    write_file(f"{cfg['slug']}.html", page_shell(
        f"{cfg['slug']}.html", f"{hero_title} | {NAMA_BISNIS}", cfg["meta_description"], body, schema,
    ))

# ---------------------------------------------------------------------------
# sitemap.xml & robots.txt -- di-generate otomatis dari daftar halaman yang
# BENAR-BENAR baru saja ditulis, dan selalu pakai SITE_BASE_URL yang aktif.
# Ini mencegah sitemap "nyasar" ke domain lama saat SITE_BASE_URL diganti
# (misalnya waktu pindah dari GitHub Pages ke domain sendiri).
# ---------------------------------------------------------------------------
ALL_SLUGS = (
    ["index.html", "blog.html"]
    + [f"{cfg['slug']}.html" for cfg in LAYANAN_CONFIG]
    + [f"{field(r, 'Slug URL')}.html" for r in studi_kasus_rows]
    + [f"{field(r, 'Slug URL')}.html" for r in artikel_rows]
)

sitemap_entries = "\n".join(
    f"  <url><loc>{SITE_BASE_URL}/{slug}</loc></url>" for slug in ALL_SLUGS
)
sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_entries}
</urlset>
"""
write_file("sitemap.xml", sitemap_xml)

robots_txt = f"""User-agent: *
Allow: /

Sitemap: {SITE_BASE_URL}/sitemap.xml
"""
write_file("robots.txt", robots_txt)

print(f"Selesai. {len(studi_kasus_rows)} studi kasus + {len(artikel_rows)} artikel + {len(LAYANAN_CONFIG)} halaman layanan diterbitkan.")
