#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator website Kreasi Digital (v3) -- Airtable -> HTML statis untuk GitHub Pages.

Alur kerja:
1. Baca semua tabel dari base Airtable "CMS Website Kreasi Digital".
2. Bangun halaman dua bahasa:
     Bahasa Indonesia  : /, /solusi/..., /untuk/..., /studi-kasus/..., /blog/...
     English           : /en/, /en/solutions/..., /en/for/..., /en/case-studies/..., /en/blog/...
   Setiap halaman punya tombol ID/EN yang menaut ke pasangannya (hreflang).
3. Tulis halaman pengalihan untuk URL lama (jasa-website-bali.html, dll.),
   sitemap.xml (dengan hreflang), robots.txt, 404.html, dan assets/site.css.
4. Hapus halaman yang dulu dibuat script ini tapi sekarang tidak diterbitkan
   lagi (misalnya studi kasus yang diubah ke Draft).

ENV VARS (GitHub Actions secrets):
- AIRTABLE_API_KEY  : Personal Access Token (scope data.records:read, akses ke base baru)
- AIRTABLE_BASE_ID  : ID base "CMS Website Kreasi Digital" (apptiqj9Z0vnDBJop)
- SITE_BASE_URL     : alamat situs tanpa garis miring di akhir.
                      Sekarang : https://hi-kreasidigital.github.io/kreasi-digital-site
                      Nanti    : https://www.domainanda.com
- BASE_PATH         : "/kreasi-digital-site" selama masih di github.io,
                      KOSONGKAN setelah pakai domain sendiri.
Opsional:
- NEWSLETTER_WEBHOOK_URL : URL webhook Airtable Automation untuk form newsletter.
- AIRTABLE_SNAPSHOT_DIR  : (untuk tes lokal) folder berisi <Nama Tabel>.json,
                           dipakai sebagai pengganti Airtable API.
"""
import os
import re
import json
import urllib.request
import urllib.parse
from datetime import date

from site_text import DEFAULT_TEXT

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------
REPO_ROOT = os.environ.get("REPO_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAPSHOT_DIR = os.environ.get("AIRTABLE_SNAPSHOT_DIR", "").strip()
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID") or "apptiqj9Z0vnDBJop"
SITE_BASE_URL = (os.environ.get("SITE_BASE_URL") or "https://hi-kreasidigital.github.io/kreasi-digital-site").rstrip("/")
BASE_PATH = (os.environ.get("BASE_PATH") or "").rstrip("/")
if BASE_PATH and not BASE_PATH.startswith("/"):
    BASE_PATH = "/" + BASE_PATH

# Form newsletter mengirim ke webhook Airtable Automation. URL webhook hanya bisa
# MENAMBAH pendaftar, tidak bisa membaca/mengubah data, jadi aman tampil di HTML.
# Secret kosong = pakai URL default di bawah. Isi "off" untuk menyembunyikan form.
NEWSLETTER_WEBHOOK_URL = (os.environ.get("NEWSLETTER_WEBHOOK_URL") or
    "https://hooks.airtable.com/workflows/v1/genericWebhook/appTgtEPUl5kIRHvv/wfl1Fy5OOp9d7I8Rz/wtr6q8E91WOTrCTcK").strip()
if NEWSLETTER_WEBHOOK_URL.lower() == "off":
    NEWSLETTER_WEBHOOK_URL = ""

GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "Zm8rUHDS_EffoluHuIbreulEjK4y8wek20QiN7TyTIE").strip()

LANGS = ("id", "en")
HTML_LANG = {"id": "id", "en": "en"}
OG_LOCALE = {"id": "id_ID", "en": "en_US"}
PREFIX = {"id": "", "en": "/en"}
SEG = {
    "solusi": {"id": "solusi", "en": "solutions"},
    "untuk": {"id": "untuk", "en": "for"},
    "studi": {"id": "studi-kasus", "en": "case-studies"},
    "blog": {"id": "blog", "en": "blog"},
}
SUFFIX = {"id": "ID", "en": "EN"}

TABLES = {
    "teks": "Teks Situs",
    "masalah": "Masalah Bisnis",
    "audiens": "Audiens",
    "masalah_audiens": "Masalah per Audiens",
    "studi": "Studi Kasus",
    "artikel": "Artikel Blog",
    "faq": "FAQ",
    "proses": "Proses Kerja",
    "tim": "Tim",
    "kontak": "Kontak",
    "sosmed": "Sosial Media",
}

# Gambar bawaan di repo (dipakai kalau kolom gambar di Airtable kosong)
FALLBACK_CASE_IMAGE = {
    "rekap-data-warga": "/assets/img/case-rekap-data-warga.webp",
    "nota-pos": "/assets/img/case-nota-pos.webp",
    "outreach-cafe-resto": "/assets/img/case-outreach-cafe-resto.webp",
    "bali-island-driver": "/assets/img/case-bali-island-driver.webp",
    "aussie-souvenirs": "/assets/img/case-aussie-souvenirs.webp",
    "pride-on": "/assets/img/case-pride-on.webp",
    "tattoo-in-bali": "/assets/img/case-tattoo-in-bali.webp",
}
FALLBACK_TEAM_PHOTO = {"Tara": "/assets/img/team-tara.webp", "Mattel": "/assets/img/team-mattel.webp"}
LOGO = "/assets/img/logo.png"
HERO_IMG = "/assets/img/hero-illustration.webp"
APP_ILLU_IMG = "/assets/img/app-illustration.webp"
OG_IMAGE = "/assets/img/og-cover.jpg"

# URL lama (website v2) -> URL baru. Halaman pengalihan dibuat otomatis.
LEGACY_REDIRECTS = {
    "blog.html": "/blog/",
    "jasa-website-bali.html": "/solusi/",
    "jasa-kasir-digital-malang.html": "/solusi/stok-dan-penjualan/",
    "dashboard-sistem-umkm.html": "/solusi/data-anggota-dan-warga/",
    "studi-kasus-rekap-warga.html": "/studi-kasus/rekap-data-warga/",
    "studi-kasus-nota-pos.html": "/studi-kasus/nota-pos/",
    "studi-kasus-outreach-cafe-malang.html": "/studi-kasus/outreach-cafe-resto/",
    "studi-kasus-bali-island-driver.html": "/studi-kasus/bali-island-driver/",
    "studi-kasus-aussie-souvenirs.html": "/studi-kasus/aussie-souvenirs/",
    "studi-kasus-pride-on.html": "/studi-kasus/pride-on/",
    "studi-kasus-tattoo-in-bali.html": "/studi-kasus/tattoo-in-bali/",
    "artikel-pentingnya-kasir-digital-umkm.html": "/blog/kasir-digital-untuk-umkm/",
    "artikel-tips-pilih-jasa-website-umkm-bali.html": "/blog/",
}

MANIFEST = ".generated-files.json"


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------
def airtable_get(table_name):
    """Ambil semua record sebuah tabel (format REST: {'id', 'fields': {nama: nilai}})."""
    if SNAPSHOT_DIR:
        path = os.path.join(SNAPSHOT_DIR, f"{table_name}.json")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if not AIRTABLE_API_KEY:
        raise SystemExit("AIRTABLE_API_KEY belum diisi.")
    records, offset = [], None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        url = f"https://api.airtable.com/v0/{BASE_ID}/{urllib.parse.quote(table_name)}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            return records


def F(rec, name, default=""):
    v = rec.get("fields", {}).get(name, default)
    return default if v is None else v


def FL(rec, base, lang, fallback=True):
    """Field berbahasa: '<base> ID' / '<base> EN'. EN kosong -> pakai ID (kalau fallback)."""
    v = F(rec, f"{base} {SUFFIX[lang]}")
    if isinstance(v, str):
        v = v.strip()
    if not v and lang == "en" and fallback:
        v = F(rec, f"{base} ID")
        if isinstance(v, str):
            v = v.strip()
    return v


def order_key(rec):
    v = F(rec, "Urutan", None)
    return (v if isinstance(v, (int, float)) else 9999)


def published(rows):
    return [r for r in rows if F(r, "Status") == "Published"]


def lines(text):
    return [l.strip().lstrip("-•").strip() for l in (text or "").split("\n") if l.strip()]


# ---------------------------------------------------------------------------
# Helpers HTML
# ---------------------------------------------------------------------------
def esc(s):
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def hl(s):
    """*kata* -> stabilo kuning."""
    return re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', esc(s))


def plain(s):
    return re.sub(r"\*(.+?)\*", r"\1", s or "")


def inline_md(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)",
               lambda m: f'<a href="{m.group(2) if m.group(2).startswith("http") else u(m.group(2))}">{m.group(1)}</a>', s)
    return s


def md_to_html(text):
    """Markdown mini: paragraf (baris kosong), '## ', '### ', '- ' list, '1. ' list, **tebal**, [tautan](url)."""
    out = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        blines = [l.rstrip() for l in block.strip().split("\n") if l.strip()]
        if not blines:
            continue
        # sub-blok: judul di baris pertama diikuti isi
        buf = []

        def flush_para():
            if buf:
                out.append("<p>" + " ".join(inline_md(x) for x in buf) + "</p>")
                buf.clear()

        i = 0
        while i < len(blines):
            ln = blines[i].strip()
            if ln.startswith("### "):
                flush_para(); out.append(f"<h3>{inline_md(ln[4:])}</h3>"); i += 1
            elif ln.startswith("## "):
                flush_para(); out.append(f"<h2>{inline_md(ln[3:])}</h2>"); i += 1
            elif re.match(r"^[-*] ", ln):
                flush_para(); items = []
                while i < len(blines) and re.match(r"^[-*] ", blines[i].strip()):
                    items.append(inline_md(blines[i].strip()[2:])); i += 1
                out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            elif re.match(r"^\d+[.)] ", ln):
                flush_para(); items = []
                while i < len(blines) and re.match(r"^\d+[.)] ", blines[i].strip()):
                    items.append(inline_md(re.sub(r"^\d+[.)] ", "", blines[i].strip()))); i += 1
                out.append("<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>")
            else:
                buf.append(ln); i += 1
        flush_para()
    return "\n".join(out)


def paragraphs(text):
    return "".join(f"<p>{inline_md(p.strip())}</p>" for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip())


def u(path):
    """URL internal (menghormati BASE_PATH untuk github.io/nama-repo)."""
    if not path or path.startswith(("http://", "https://", "#", "mailto:", "tel:")):
        return path
    return f"{BASE_PATH}{path}"


def abs_url(path):
    if path.startswith("http"):
        return path
    return f"{SITE_BASE_URL}{path}"


def route(kind, lang, slug=None):
    if kind == "home":
        return PREFIX[lang] + "/"
    base = f"{PREFIX[lang]}/{SEG[kind][lang]}/"
    return base + (f"{slug}/" if slug else "")


def out_file(path):
    p = path.strip("/")
    return "index.html" if not p else f"{p}/index.html"


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "halaman"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
RAW = {k: airtable_get(v) for k, v in TABLES.items()}

TEXT_ROWS = {F(r, "Key"): r for r in RAW["teks"] if F(r, "Key")}


def T(key, lang):
    r = TEXT_ROWS.get(key)
    if r:
        v = (F(r, f"Teks {SUFFIX[lang]}") or "").strip()
        if v:
            return v
        if lang == "en":
            v = (F(r, "Teks ID") or "").strip()
    d = DEFAULT_TEXT.get(key)
    if d:
        return d[0] if lang == "id" else d[1]
    return key


KONTAK = RAW["kontak"][0] if RAW["kontak"] else {"fields": {}}
NAMA = F(KONTAK, "Nama Bisnis", "Kreasi Digital") or "Kreasi Digital"
WA_NUMBER = re.sub(r"[^0-9]", "", F(KONTAK, "Nomor WhatsApp", "") or "6285117732474")
EMAIL = F(KONTAK, "Email", "hi.kreasi.digital@gmail.com")

MASALAH = sorted(published(RAW["masalah"]), key=order_key)
AUDIENS = sorted(published(RAW["audiens"]), key=order_key)
STUDI = sorted(published(RAW["studi"]), key=order_key)
ARTIKEL = sorted(published(RAW["artikel"]), key=lambda r: F(r, "Tanggal Terbit", "") or "", reverse=True)
FAQ = sorted(RAW["faq"], key=order_key)
PROSES = sorted(RAW["proses"], key=order_key)
TIM = sorted(RAW["tim"], key=order_key)
SOSMED = sorted(RAW["sosmed"], key=order_key)
MASALAH_AUDIENS = sorted(RAW["masalah_audiens"], key=order_key)

BY_ID = {}
for key in ("masalah", "audiens", "studi", "artikel"):
    for r in RAW[key]:
        BY_ID[r["id"]] = r
PUBLISHED_IDS = {r["id"] for r in MASALAH + AUDIENS + STUDI + ARTIKEL}


def links(rec, field_name):
    """Record tertaut yang Published saja, urut sesuai Urutan."""
    ids = F(rec, field_name, []) or []
    recs = [BY_ID[i] for i in ids if i in BY_ID and i in PUBLISHED_IDS]
    return sorted(recs, key=order_key)


def has_en(rec, base):
    return bool((F(rec, f"{base} EN") or "").strip())


def slug_of(rec, lang, kind):
    if kind == "studi":
        return F(rec, "Slug") or slugify(F(rec, "Judul Proyek"))
    s = (F(rec, f"Slug {SUFFIX[lang]}") or "").strip()
    if not s:
        if kind == "masalah":
            s = slugify(FL(rec, "Judul Masalah", lang))
        elif kind == "audiens":
            s = slugify(FL(rec, "Nama", lang))
        else:
            s = slugify(FL(rec, "Judul", lang))
    return s


def path_masalah(r, lang):
    if lang == "en" and not has_en(r, "Judul Masalah"):
        return None
    return route("solusi", lang, slug_of(r, lang, "masalah"))


def path_audiens(r, lang):
    if lang == "en" and not has_en(r, "Nama"):
        return None
    return route("untuk", lang, slug_of(r, lang, "audiens"))


def path_studi(r, lang):
    if lang == "en" and not (has_en(r, "Masalah Bisnis") or has_en(r, "Ringkasan")):
        return None
    return route("studi", lang, slug_of(r, lang, "studi"))


def path_artikel(r, lang):
    if lang == "en" and not has_en(r, "Judul"):
        return None
    return route("blog", lang, slug_of(r, lang, "artikel"))


# ---------------------------------------------------------------------------
# Attachment (gambar dari Airtable) -> disimpan ke repo, karena URL attachment
# Airtable kedaluwarsa setelah beberapa jam.
# ---------------------------------------------------------------------------
def localize_attachment(rec, field_name, fallback):
    atts = F(rec, field_name, []) or []
    if not atts or not isinstance(atts, list) or not atts[0].get("url"):
        return fallback
    att = atts[0]
    ext = os.path.splitext(att.get("filename") or "")[1].lower() or ".jpg"
    rel = f"/assets/uploads/{att.get('id', 'file')}{ext}"
    full = os.path.join(REPO_ROOT, rel.lstrip("/"))
    if SNAPSHOT_DIR:
        return fallback
    if not os.path.exists(full):
        try:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with urllib.request.urlopen(att["url"]) as resp, open(full, "wb") as f:
                f.write(resp.read())
        except Exception as e:  # jangan gagalkan build hanya karena satu gambar
            print("  ! gagal unduh gambar", att.get("filename"), e)
            return fallback
    GENERATED.add(rel.lstrip("/"))
    return rel


def case_image(r):
    slug = F(r, "Slug")
    fb = FALLBACK_CASE_IMAGE.get(slug, OG_IMAGE)
    return localize_attachment(r, "Gambar Cover", fb)


# ---------------------------------------------------------------------------
# Komponen
# ---------------------------------------------------------------------------
ICON = {
    "wa": '<svg viewBox="0 0 448 512" aria-hidden="true"><path fill="currentColor" d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3 18.6-68.1-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-32.6-16.3-54-29.1-75.5-66-5.7-9.8 5.7-9.1 16.3-30.3 1.8-3.7.9-6.9-.5-9.7-1.4-2.8-12.5-30.1-17.1-41.2-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 35.2 15.2 49 16.5 66.6 13.9 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>',
    "arrow": '<svg viewBox="0 0 20 20" aria-hidden="true"><path fill="currentColor" d="M11.3 4.3a1 1 0 0 1 1.4 0l5 5a1 1 0 0 1 0 1.4l-5 5a1 1 0 1 1-1.4-1.4l3.3-3.3H3a1 1 0 1 1 0-2h11.6l-3.3-3.3a1 1 0 0 1 0-1.4z"/></svg>',
    "check": '<svg viewBox="0 0 20 20" aria-hidden="true"><path fill="currentColor" d="M16.7 5.3a1 1 0 0 1 0 1.4l-8 8a1 1 0 0 1-1.4 0l-4-4a1 1 0 1 1 1.4-1.4l3.3 3.3 7.3-7.3a1 1 0 0 1 1.4 0z"/></svg>',
    "store": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M3 9l1.5-5h15L21 9M3 9h18M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 12v8h14v-8M10 20v-5h4v5"/></svg>',
    "school": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M12 3l9 5-9 5-9-5 9-5zM6 10v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5M21 8v6"/></svg>',
    "people": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21v-1a6 6 0 0 1 6-6h2a6 6 0 0 1 6 6v1M16 3.1a4 4 0 0 1 0 7.8M22 21v-1a6 6 0 0 0-4-5.7"/></svg>',
    "quote": '<svg viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M9.3 6C5.3 8 3 11.5 3 16.3V26h9v-9H7.2c0-3.4 1.6-5.8 4.3-7.2L9.3 6zm15 0c-4 2-6.3 5.5-6.3 10.3V26h9v-9h-4.8c0-3.4 1.6-5.8 4.3-7.2L24.3 6z"/></svg>',
}
AUD_ICONS = ["store", "school", "people"]


def wa_link(lang, msg=None):
    text = msg or T("wa.default", lang)
    return f"https://wa.me/{WA_NUMBER}?text={urllib.parse.quote(text)}"


def btn_wa(lang, label, msg=None, cls="btn btn-primary"):
    return (f'<a class="{cls}" href="{wa_link(lang, msg)}" target="_blank" rel="noopener">'
            f'<span class="ico">{ICON["wa"]}</span>{esc(label)}</a>')


def section_head(tag, title, sub="", center=True, h="h2"):
    cls = "section-head center" if center else "section-head"
    eyebrow = f'<span class="eyebrow">{esc(tag)}</span>' if tag else ""
    return (f'<div class="{cls}">{eyebrow}'
            f'<{h} class="section-title">{hl(title)}</{h}>'
            + (f'<p class="section-sub">{esc(sub)}</p>' if sub else "") + "</div>")


def card_masalah(r, lang, compact=False):
    href = path_masalah(r, lang)
    if not href:
        return ""
    quote = FL(r, "Kutipan Kartu", lang) or FL(r, "Judul Masalah", lang)
    return (f'<a class="problem-card" href="{u(href)}">'
            f'<span class="q-ico">{ICON["quote"]}</span>'
            f'<p class="problem-quote">{esc(quote.strip(chr(34)))}</p>'
            f'<span class="text-link">{esc(T("link.solusi", lang))} {ICON["arrow"]}</span></a>')


def card_studi(r, lang):
    href = path_studi(r, lang)
    if not href:
        return ""
    img = case_image(r)
    title = FL(r, "Masalah Bisnis", lang) or F(r, "Judul Proyek")
    return (f'<article class="case-card"><a href="{u(href)}" class="case-link">'
            f'<div class="case-img"><img src="{u(img)}" alt="{esc(F(r, "Judul Proyek"))}" loading="lazy" width="600" height="340"></div>'
            f'<div class="case-body"><span class="chip">{esc(F(r, "Judul Proyek"))}</span>'
            f'<h3>{esc(title)}</h3><p>{esc(FL(r, "Ringkasan", lang))}</p>'
            f'<span class="text-link">{esc(T("link.studi", lang))} {ICON["arrow"]}</span></div></a></article>')


def card_artikel(r, lang):
    href = path_artikel(r, lang)
    if not href:
        return ""
    img = localize_attachment(r, "Gambar Cover", "")
    img_html = (f'<div class="case-img"><img src="{u(img)}" alt="" loading="lazy" width="600" height="340"></div>' if img else "")
    return (f'<article class="case-card article-card"><a href="{u(href)}" class="case-link">{img_html}'
            f'<div class="case-body"><span class="chip">{esc(T("label.artikel", lang))}</span>'
            f'<h3>{esc(FL(r, "Judul", lang))}</h3><p>{esc(FL(r, "Ringkasan", lang))}</p>'
            f'<span class="text-link">{esc(T("link.artikel", lang))} {ICON["arrow"]}</span></div></a></article>')


def cta_band(lang, title=None, text=None, btn=None, msg=None):
    return (f'<section class="cta-band"><div class="container cta-inner">'
            f'<div><h2>{hl(title or T("cta.h2", lang))}</h2><p>{esc(text or T("cta.p", lang))}</p></div>'
            f'{btn_wa(lang, btn or T("cta.btn", lang), msg, "btn btn-primary btn-lg")}</div></section>')


def newsletter(lang, source):
    if not NEWSLETTER_WEBHOOK_URL:
        return ""
    cfg = json.dumps({
        "url": NEWSLETTER_WEBHOOK_URL, "source": source, "lang": lang,
        "invalid": T("nl.invalid", lang), "sending": T("nl.sending", lang),
        "ok": T("nl.ok", lang), "err": T("nl.err", lang),
    }, ensure_ascii=False)
    return f"""<section class="newsletter"><div class="container nl-inner">
  <div><span class="eyebrow">{esc(T("nl.tag", lang))}</span><h2>{hl(T("nl.h2", lang))}</h2><p>{esc(T("nl.p", lang))}</p></div>
  <form class="nl-form" data-nl="{esc(cfg)}" novalidate>
    <label class="sr-only" for="nl-email">Email</label>
    <input id="nl-email" type="email" name="email" placeholder="{esc(T("nl.placeholder", lang))}" autocomplete="email" required>
    <div class="nl-trap" aria-hidden="true"><label for="nl-website">Website</label><input id="nl-website" type="text" name="website" tabindex="-1" autocomplete="off"></div>
    <button type="submit" class="btn btn-dark">{esc(T("nl.btn", lang))}</button>
    <p class="nl-msg" role="status"></p>
  </form>
</div></section>"""


# ---------------------------------------------------------------------------
# Layout (header, footer, shell)
# ---------------------------------------------------------------------------
def header(lang, alts):
    other = "en" if lang == "id" else "id"
    other_path = alts.get(other) or route("home", other)
    here = alts.get(lang) or route("home", lang)
    nav = [
        (route("solusi", lang), T("nav.solusi", lang)),
        (route("untuk", lang), T("nav.untuk", lang)),
        (route("studi", lang), T("nav.studi", lang)),
        (route("blog", lang), T("nav.blog", lang)),
        (route("home", lang) + "#tentang", T("nav.tentang", lang)),
    ]
    cur = ' aria-current="page"'
    act = ' class="active" aria-current="true"'
    home_p = route("home", lang)
    items = "".join(
        f'<li><a href="{u(p)}"{cur if (p != home_p + "#tentang" and here.startswith(p)) else ""}>{esc(t)}</a></li>'
        for p, t in nav)
    lang_sw = (f'<div class="lang-switch" role="group" aria-label="Language">'
               f'<a href="{u(alts.get("id") or route("home", "id"))}" hreflang="id" lang="id"{act if lang == "id" else ""}>ID</a>'
               f'<a href="{u(alts.get("en") or route("home", "en"))}" hreflang="en" lang="en"{act if lang == "en" else ""}>EN</a></div>')
    return f"""<a class="skip" href="#main">{"Langsung ke isi" if lang == "id" else "Skip to content"}</a>
<header class="site-header"><div class="container nav-wrap">
  <a href="{u(route("home", lang))}" class="brand"><img src="{u(LOGO)}" alt="{esc(NAMA)}" width="68" height="60"></a>
  <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span><span class="sr-only">Menu</span></button>
  <nav id="site-nav" class="site-nav"><ul>{items}</ul>
    {lang_sw}
    {btn_wa(lang, T("nav.cta", lang), None, "btn btn-primary btn-sm")}
  </nav>
</div></header>"""


def footer(lang):
    sol = "".join(f'<li><a href="{u(path_masalah(m, lang))}">{esc(plain(FL(m, "Judul Masalah", lang)).rstrip("?"))}</a></li>'
                  for m in MASALAH[:6] if path_masalah(m, lang))
    aud = "".join(f'<li><a href="{u(path_audiens(a, lang))}">{esc(FL(a, "Nama", lang))}</a></li>'
                  for a in AUDIENS if path_audiens(a, lang))
    icons = []
    for s in SOSMED:
        link = F(s, "Link")
        if not link:
            continue
        logo = localize_attachment(s, "Logo", "")
        inner = f'<img src="{u(logo)}" alt="" width="20" height="20">' if logo else esc(F(s, "Platform")[:2])
        icons.append(f'<a href="{esc(link)}" target="_blank" rel="noopener" class="soc" aria-label="{esc(F(s, "Platform"))}">{inner}</a>')
    soc = f'<div class="soc-row">{"".join(icons)}</div>' if icons else f'<p class="muted-dark">{esc(T("footer.sosmed_kosong", lang))}</p>'
    area = FL(KONTAK, "Area Layanan", lang)
    return f"""<footer class="site-footer"><div class="container">
  <div class="footer-grid">
    <div class="footer-about">
      <img src="{u(LOGO)}" alt="{esc(NAMA)}" width="68" height="60">
      <p>{esc(T("footer.text", lang))}</p>
      <p class="small"><strong>{esc(T("footer.area", lang))}:</strong> {esc(area)}<br>
      <strong>Email:</strong> <a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a></p>
    </div>
    <div><h4>{esc(T("footer.col_solusi", lang))}</h4><ul>{sol}<li><a href="{u(route("solusi", lang))}">{esc(T("nav.solusi", lang))} →</a></li></ul></div>
    <div><h4>{esc(T("footer.col_untuk", lang))}</h4><ul>{aud}</ul><h4 style="margin-top:22px">{esc(T("footer.col_sosmed", lang))}</h4>{soc}</div>
  </div>
  <div class="footer-bottom"><span>&copy; {date.today().year} {esc(NAMA)}</span><span>{esc(T("footer.tagline", lang))}</span></div>
</div></footer>
<a href="{wa_link(lang)}" class="wa-float" target="_blank" rel="noopener" aria-label="WhatsApp">{ICON["wa"]}</a>"""


def breadcrumb_html(items):
    if not items:
        return ""
    parts = []
    for name, href in items:
        parts.append(f'<a href="{u(href)}">{esc(name)}</a>' if href else f'<span aria-current="page">{esc(name)}</span>')
    sep = ' <span class="sep">/</span> '
    return f'<nav class="crumbs container" aria-label="Breadcrumb">{sep.join(parts)}</nav>'


def breadcrumb_schema(items, lang, current_path):
    lst = []
    for i, (name, href) in enumerate(items, start=1):
        lst.append({"@type": "ListItem", "position": i, "name": plain(name), "item": abs_url(href or current_path)})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lst}


ORG_SCHEMA = None


def org_schema():
    same = [F(s, "Link") for s in SOSMED if F(s, "Link")]
    d = {
        "@context": "https://schema.org", "@type": "ProfessionalService",
        "@id": abs_url("/#organization"), "name": NAMA, "url": abs_url("/"),
        "logo": abs_url(LOGO), "image": abs_url(OG_IMAGE), "email": EMAIL,
        "telephone": "+" + WA_NUMBER, "areaServed": [{"@type": "Country", "name": "Indonesia"}],
        "description": plain(T("home.meta", "id")),
        "knowsAbout": [plain(FL(m, "Judul Masalah", "id")) for m in MASALAH],
    }
    if same:
        d["sameAs"] = same
    return d


def shell(lang, path, alts, title, description, body, schemas=(), crumbs=None, og_image=None, og_type="website", noindex=False):
    canonical = abs_url(path)
    alt_links = ""
    if alts.get("id") and alts.get("en"):
        alt_links = (f'<link rel="alternate" hreflang="id" href="{abs_url(alts["id"])}">\n'
                     f'<link rel="alternate" hreflang="en" href="{abs_url(alts["en"])}">\n'
                     f'<link rel="alternate" hreflang="x-default" href="{abs_url(alts["id"])}">')
    schema_html = "\n".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas if s)
    gsv = f'<meta name="google-site-verification" content="{esc(GOOGLE_SITE_VERIFICATION)}">' if GOOGLE_SITE_VERIFICATION else ""
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    ogi = abs_url(og_image or OG_IMAGE)
    return f"""<!DOCTYPE html>
<html lang="{HTML_LANG[lang]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(plain(title))}</title>
<meta name="description" content="{esc(plain(description))}">
{robots}{gsv}
<link rel="canonical" href="{canonical}">
{alt_links}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(NAMA)}">
<meta property="og:locale" content="{OG_LOCALE[lang]}">
<meta property="og:title" content="{esc(plain(title))}">
<meta property="og:description" content="{esc(plain(description))}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{ogi}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FEBF23">
<link rel="icon" href="{u(LOGO)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{u('/assets/site.css')}?v={CSS_VERSION}">
{schema_html}
</head>
<body>
{header(lang, alts)}
<main id="main">
{breadcrumb_html(crumbs)}
{body}
</main>
{footer(lang)}
<script src="{u('/assets/site.js')}?v={CSS_VERSION}" defer></script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
GENERATED = set()
SITEMAP = []  # (path, alts)


def write_file(rel, content):
    full = os.path.join(REPO_ROOT, rel)
    os.makedirs(os.path.dirname(full) or REPO_ROOT, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    GENERATED.add(rel)


def emit(path, lang, alts, html, in_sitemap=True):
    write_file(out_file(path), html)
    if in_sitemap:
        SITEMAP.append((path, alts))


# ---------------------------------------------------------------------------
# Halaman: Beranda
# ---------------------------------------------------------------------------
def page_home(lang):
    alts = {l: route("home", l) for l in LANGS}
    path = alts[lang]
    problems = "".join(card_masalah(m, lang) for m in MASALAH)
    aud_cards = []
    for i, a in enumerate(AUDIENS):
        href = path_audiens(a, lang)
        if not href:
            continue
        ic = ICON[AUD_ICONS[i % len(AUD_ICONS)]]
        aud_cards.append(f'<a class="aud-card" href="{u(href)}"><span class="aud-ico">{ic}</span>'
                         f'<h3>{esc(FL(a, "Nama", lang))}</h3><p>{esc(FL(a, "Deskripsi Kartu", lang))}</p>'
                         f'<span class="text-link">{esc(FL(a, "Nama", lang))} {ICON["arrow"]}</span></a>')
    steps = "".join(f'<li class="step"><span class="step-num">{i}</span><h3>{esc(FL(p, "Judul", lang))}</h3>'
                    f'<p>{esc(FL(p, "Deskripsi", lang))}</p></li>' for i, p in enumerate(PROSES, start=1))
    poin = "".join(f'<li><span class="tick">{ICON["check"]}</span>{esc(x)}</li>' for x in lines(T("sec.kenapa.poin", lang)))
    team = "".join(
        f'<div class="member"><img src="{u(localize_attachment(t, "Foto", FALLBACK_TEAM_PHOTO.get(F(t, "Nama"), LOGO)))}" alt="{esc(F(t, "Nama"))}" width="96" height="96" loading="lazy">'
        f'<div><strong>{esc(F(t, "Nama"))}</strong><span>{esc(FL(t, "Jabatan", lang))}</span></div></div>' for t in TIM)
    home_cases = [c for c in STUDI if F(c, "Tampil di Beranda")][:6] or STUDI[:6]
    cases = "".join(card_studi(c, lang) for c in home_cases)

    body = f"""<section class="hero"><div class="container hero-grid">
  <div class="hero-copy">
    <span class="eyebrow">{esc(T("hero.tag", lang))}</span>
    <h1>{hl(T("hero.h1", lang))}</h1>
    <p class="lead">{esc(T("hero.sub", lang))}</p>
    <div class="btn-row">{btn_wa(lang, T("hero.cta1", lang), None, "btn btn-primary btn-lg")}
      <a class="btn btn-ghost btn-lg" href="{u(route("solusi", lang))}">{esc(T("hero.cta2", lang))}</a></div>
  </div>
  <div class="hero-art"><img src="{u(HERO_IMG)}" alt="" width="600" height="338" fetchpriority="high"></div>
</div></section>
<section class="promise"><div class="container"><p class="promise-h">{hl(T("banner.h", lang))}</p><p>{esc(T("banner.p", lang))}</p></div></section>
<section class="section" id="masalah"><div class="container">
  {section_head(T("sec.masalah.tag", lang), T("sec.masalah.h2", lang))}
  <div class="problem-grid">{problems}</div>
  <div class="closing"><p>{esc(T("sec.masalah.penutup", lang))}</p>{btn_wa(lang, T("sec.masalah.cta", lang), None, "btn btn-dark")}</div>
</div></section>
<section class="section tint" id="untuk"><div class="container">
  {section_head(T("sec.untuk.tag", lang), T("sec.untuk.h2", lang))}
  <div class="aud-grid">{"".join(aud_cards)}</div>
</div></section>
<section class="illu-band"><div class="container">
  <img src="{u(APP_ILLU_IMG)}" alt="{esc(T("illu.alt", lang))}" width="900" height="843" loading="lazy">
</div></section>
<section class="section" id="proses"><div class="container">
  {section_head(T("sec.proses.tag", lang), T("sec.proses.h2", lang))}
  <ol class="steps">{steps}</ol>
</div></section>
<section class="section tint" id="tentang"><div class="container about-grid">
  <div>{section_head(T("sec.kenapa.tag", lang), T("sec.kenapa.h2", lang), center=False)}
    <p class="lead-sm">{esc(T("sec.kenapa.p", lang))}</p><ul class="ticks">{poin}</ul></div>
  <div class="team">{team}</div>
</div></section>
<section class="section" id="studi-kasus"><div class="container">
  {section_head(T("sec.studi.tag", lang), T("sec.studi.h2", lang))}
  <div class="case-grid">{cases}</div>
  <div class="center mt"><a class="btn btn-ghost" href="{u(route("studi", lang))}">{esc(T("sec.studi.all", lang))}</a></div>
</div></section>
{cta_band(lang)}
{newsletter(lang, "Beranda" if lang == "id" else "Home (EN)")}"""
    website = {"@context": "https://schema.org", "@type": "WebSite", "name": NAMA, "url": abs_url("/"),
               "inLanguage": ["id", "en"]}
    emit(path, lang, alts, shell(lang, path, alts, T("home.title", lang), T("home.meta", lang), body,
                                 schemas=[org_schema(), website]))


# ---------------------------------------------------------------------------
# Halaman: Solusi (hub + detail)
# ---------------------------------------------------------------------------
def related_problems(current, lang, limit=6):
    others = [m for m in MASALAH if m["id"] != current["id"] and path_masalah(m, lang)]
    cur_aud = set(F(current, "Audiens", []) or [])
    others.sort(key=lambda m: (0 if cur_aud & set(F(m, "Audiens", []) or []) else 1, order_key(m)))
    return others[:limit]


def page_solusi_hub(lang):
    alts = {l: route("solusi", l) for l in LANGS}
    path = alts[lang]
    groups = []
    shown = set()
    for a in AUDIENS:
        items = [m for m in MASALAH if a["id"] in (F(m, "Audiens", []) or []) and path_masalah(m, lang)]
        if not items:
            continue
        cards = "".join(card_masalah(m, lang) for m in items)
        shown.update(m["id"] for m in items)
        groups.append(f'<div class="group"><h2 class="group-title"><a href="{u(path_audiens(a, lang) or route("untuk", lang))}">{esc(FL(a, "Nama", lang))}</a></h2>'
                      f'<div class="problem-grid">{cards}</div></div>')
    rest = [m for m in MASALAH if m["id"] not in shown and path_masalah(m, lang)]
    if rest:
        groups.append(f'<div class="group"><div class="problem-grid">{"".join(card_masalah(m, lang) for m in rest)}</div></div>')
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.solusi", lang), None)]
    body = f"""<section class="page-hero wide"><div class="container narrow">
  <h1>{hl(T("solusi.h1", lang))}</h1><p class="lead">{esc(T("solusi.sub", lang))}</p></div></section>
<section class="section pt0"><div class="container">{"".join(groups)}</div></section>
{cta_band(lang)}"""
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": abs_url(path_masalah(m, lang)), "name": plain(FL(m, "Judul Masalah", lang))}
        for i, m in enumerate([m for m in MASALAH if path_masalah(m, lang)], start=1)]}
    emit(path, lang, alts, shell(lang, path, alts, f'{T("solusi.title", lang)} | {NAMA}', T("solusi.meta", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path), itemlist], crumbs=crumbs))


def page_masalah(m, lang):
    path = path_masalah(m, lang)
    if not path:
        return
    alts = {l: path_masalah(m, l) for l in LANGS}
    title = FL(m, "Judul Masalah", lang)
    seo_title = FL(m, "Title SEO", lang) or plain(title)
    meta = FL(m, "Meta Description", lang)
    msg = FL(m, "Pesan WA", lang) or None
    auds = links(m, "Audiens")
    chips = "".join(f'<a class="chip chip-link" href="{u(path_audiens(a, lang))}">{esc(FL(a, "Nama", lang))}</a>'
                    for a in auds if path_audiens(a, lang))
    signs = "".join(f'<li><span class="tick">{ICON["check"]}</span>{esc(x)}</li>' for x in lines(FL(m, "Tanda-tanda", lang)))
    opts = []
    for i, ln in enumerate(lines(FL(m, "Pilihan Solusi", lang)), start=1):
        head, _, desc = ln.partition("::")
        opts.append(f'<li class="option"><span class="opt-num">{i}</span><h3>{esc(head.strip())}</h3><p>{esc(desc.strip())}</p></li>')
    cases = [c for c in STUDI if m["id"] in (F(c, "Halaman Solusi", []) or []) and path_studi(c, lang)]
    arts = [a for a in ARTIKEL if m["id"] in (F(a, "Halaman Solusi", []) or []) and path_artikel(a, lang)]
    faqs = [f for f in FAQ if m["id"] in (F(f, "Halaman Solusi", []) or [])]
    faq_html = "".join(f'<details class="faq"><summary>{esc(FL(f, "Pertanyaan", lang))}</summary><div>{paragraphs(FL(f, "Jawaban", lang))}</div></details>' for f in faqs)
    others = "".join(f'<li><a href="{u(path_masalah(o, lang))}">{esc(plain(FL(o, "Judul Masalah", lang)))}</a></li>' for o in related_problems(m, lang))

    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.solusi", lang), route("solusi", lang)), (plain(title).rstrip("?"), None)]
    body = f"""<section class="page-hero wide"><div class="container narrow">
  <div class="chips">{chips}</div>
  <h1>{hl(title)}</h1><p class="lead">{esc(meta)}</p>
  <div class="btn-row">{btn_wa(lang, T("solusi.cta_btn", lang), msg, "btn btn-primary btn-lg")}</div>
</div></section>
<section class="section pt0"><div class="container two-col">
  <div class="prose"><h2>{esc(T("solusi.kenapa", lang))}</h2>{paragraphs(FL(m, "Paragraf Empati", lang))}</div>
  <aside class="signs"><h2>{esc(T("solusi.tanda", lang))}</h2><ul class="ticks">{signs}</ul></aside>
</div></section>
<section class="section tint"><div class="container">
  {section_head("", T("solusi.pilihan", lang), T("solusi.pilihan_sub", lang))}
  <ol class="options">{"".join(opts)}</ol>
</div></section>
{f'<section class="section"><div class="container">{section_head(T("sec.studi.tag", lang), T("solusi.bukti", lang))}<div class="case-grid">{"".join(card_studi(c, lang) for c in cases)}</div></div></section>' if cases else ""}
{f'<section class="section faq-sec"><div class="container narrow"><h2 class="section-title">{esc(T("solusi.faq", lang))}</h2>{faq_html}</div></section>' if faqs else ""}
{f'<section class="section pt0"><div class="container">{section_head(T("label.artikel", lang), T("solusi.artikel", lang))}<div class="case-grid">{"".join(card_artikel(a, lang) for a in arts)}</div></div></section>' if arts else ""}
{cta_band(lang, T("solusi.cta_h", lang), T("solusi.cta_p", lang), T("solusi.cta_btn", lang), msg)}
<section class="section"><div class="container narrow"><h2 class="section-title small-title">{esc(T("solusi.lain", lang))}</h2><ul class="link-list">{others}</ul></div></section>"""
    schemas = [breadcrumb_schema(crumbs, lang, path)]
    schemas.append({"@context": "https://schema.org", "@type": "Service", "name": plain(seo_title),
                    "description": plain(meta), "provider": {"@id": abs_url("/#organization"), "@type": "ProfessionalService", "name": NAMA},
                    "areaServed": "Indonesia", "url": abs_url(path)})
    if faqs:
        schemas.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": FL(f, "Pertanyaan", lang),
             "acceptedAnswer": {"@type": "Answer", "text": FL(f, "Jawaban", lang)}} for f in faqs]})
    emit(path, lang, alts, shell(lang, path, alts, f"{seo_title} | {NAMA}", meta, body, schemas=schemas, crumbs=crumbs))


# ---------------------------------------------------------------------------
# Halaman: Untuk siapa (hub + detail)
# ---------------------------------------------------------------------------
def page_untuk_hub(lang):
    alts = {l: route("untuk", l) for l in LANGS}
    path = alts[lang]
    cards = []
    for i, a in enumerate(AUDIENS):
        href = path_audiens(a, lang)
        if not href:
            continue
        cards.append(f'<a class="aud-card" href="{u(href)}"><span class="aud-ico">{ICON[AUD_ICONS[i % 3]]}</span>'
                     f'<h2>{esc(FL(a, "Nama", lang))}</h2><p>{esc(FL(a, "Deskripsi Kartu", lang))}</p>'
                     f'<span class="text-link">{esc(FL(a, "H1", lang))} {ICON["arrow"]}</span></a>')
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.untuk", lang), None)]
    body = f"""<section class="page-hero wide"><div class="container narrow"><h1>{hl(T("untuk.h1", lang))}</h1><p class="lead">{esc(T("untuk.sub", lang))}</p></div></section>
<section class="section pt0"><div class="container"><div class="aud-grid">{"".join(cards)}</div></div></section>
{cta_band(lang)}"""
    emit(path, lang, alts, shell(lang, path, alts, f'{T("untuk.title", lang)} | {NAMA}', T("untuk.meta", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path)], crumbs=crumbs))


def page_audiens(a, lang):
    path = path_audiens(a, lang)
    if not path:
        return
    alts = {l: path_audiens(a, l) for l in LANGS}
    rows = []
    for r in MASALAH_AUDIENS:
        if a["id"] not in (F(r, "Audiens", []) or []):
            continue
        sol = FL(r, "Solusi", lang)
        target = links(r, "Halaman Solusi")
        tpath = path_masalah(target[0], lang) if target else None
        sol_html = f'<a href="{u(tpath)}">{esc(sol)} {ICON["arrow"]}</a>' if tpath else esc(sol)
        rows.append(f'<tr><td>{esc(FL(r, "Masalah", lang))}</td><td>{sol_html}</td></tr>')
    note_h, note_p = FL(a, "Catatan Judul", lang), FL(a, "Catatan Isi", lang)
    cases = [c for c in STUDI if a["id"] in (F(c, "Audiens", []) or []) and path_studi(c, lang)][:3]
    probs = [m for m in MASALAH if a["id"] in (F(m, "Audiens", []) or []) and path_masalah(m, lang)]
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.untuk", lang), route("untuk", lang)), (FL(a, "Nama", lang), None)]
    cta_label = FL(a, "Tombol CTA", lang) or T("cta.btn", lang)
    body = f"""<section class="page-hero"><div class="container narrow">
  <span class="eyebrow">{esc(FL(a, "Nama", lang))}</span>
  <h1>{hl(FL(a, "H1", lang))}</h1><p class="lead">{esc(FL(a, "Pembuka", lang))}</p>
  <div class="btn-row">{btn_wa(lang, cta_label, None, "btn btn-primary btn-lg")}</div>
</div></section>
<section class="section pt0"><div class="container narrow">
  <h2 class="section-title small-title">{esc(FL(a, "Judul Tabel", lang))}</h2>
  <div class="table-wrap"><table class="ps-table"><thead><tr><th>{esc(T("untuk.col1", lang))}</th><th>{esc(T("untuk.col2", lang))}</th></tr></thead>
  <tbody>{"".join(rows)}</tbody></table></div>
  {f'<div class="note"><h3>{esc(note_h)}</h3><p>{esc(note_p)}</p></div>' if note_h and note_p else ""}
</div></section>
{f'<section class="section tint"><div class="container">{section_head(T("sec.masalah.tag", lang), T("solusi.title", lang))}<div class="problem-grid">{"".join(card_masalah(m, lang) for m in probs)}</div></div></section>' if probs else ""}
{f'<section class="section"><div class="container">{section_head(T("sec.studi.tag", lang), T("untuk.bukti", lang))}<div class="case-grid">{"".join(card_studi(c, lang) for c in cases)}</div></div></section>' if cases else ""}
{cta_band(lang, btn=cta_label)}"""
    title = FL(a, "Title SEO", lang) or FL(a, "Nama", lang)
    emit(path, lang, alts, shell(lang, path, alts, f"{title} | {NAMA}", FL(a, "Meta Description", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path)], crumbs=crumbs))


# ---------------------------------------------------------------------------
# Halaman: Studi kasus (hub + detail)
# ---------------------------------------------------------------------------
def page_studi_hub(lang):
    alts = {l: route("studi", l) for l in LANGS}
    path = alts[lang]
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.studi", lang), None)]
    body = f"""<section class="page-hero wide"><div class="container narrow"><h1>{hl(T("studi.h1", lang))}</h1><p class="lead">{esc(T("studi.sub", lang))}</p></div></section>
<section class="section pt0"><div class="container"><div class="case-grid">{"".join(card_studi(c, lang) for c in STUDI)}</div></div></section>
{cta_band(lang)}"""
    emit(path, lang, alts, shell(lang, path, alts, f'{T("studi.title", lang)} | {NAMA}', T("studi.meta", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path)], crumbs=crumbs))


def page_studi(c, lang):
    path = path_studi(c, lang)
    if not path:
        return
    alts = {l: path_studi(c, l) for l in LANGS}
    name = F(c, "Judul Proyek")
    problem = FL(c, "Masalah Bisnis", lang)
    img = case_image(c)
    hasil = "".join(f'<li><span class="tick">{ICON["check"]}</span>{esc(x)}</li>' for x in lines(FL(c, "Hasil", lang)))
    rel = [m for m in links(c, "Halaman Solusi") if path_masalah(m, lang)]
    rel_html = "".join(f'<li><a href="{u(path_masalah(m, lang))}">{esc(plain(FL(m, "Judul Masalah", lang)))}</a></li>' for m in rel)
    link = F(c, "Link Proyek")
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.studi", lang), route("studi", lang)), (name, None)]
    body = f"""<section class="page-hero"><div class="container narrow">
  <span class="eyebrow">{esc(T("label.studi", lang))} · {esc(name)}</span>
  <h1>{esc(problem or name)}</h1><p class="lead">{esc(FL(c, "Ringkasan", lang))}</p>
</div></section>
<section class="section pt0"><div class="container narrow">
  <figure class="cover"><img src="{u(img)}" alt="{esc(name)}" width="1200" height="660"></figure>
  <div class="prose">
    <h2>{esc(T("studi.masalah", lang))}</h2>{paragraphs(FL(c, "Tantangan", lang))}
    <h2>{esc(T("studi.solusi", lang))}</h2>{paragraphs(FL(c, "Solusi", lang))}
  </div>
  <div class="result"><h2>{esc(T("studi.hasil", lang))}</h2><ul class="ticks">{hasil}</ul></div>
  {f'<p class="mt"><a class="btn btn-ghost" href="{esc(link)}" target="_blank" rel="noopener nofollow">{esc(T("studi.kunjungi", lang))} ↗</a></p>' if link else ""}
  {f'<div class="note"><h3>{esc(T("studi.terkait", lang))}</h3><ul class="link-list">{rel_html}</ul></div>' if rel_html else ""}
</div></section>
{cta_band(lang, T("studi.cta_h", lang))}"""
    art = {"@context": "https://schema.org", "@type": "Article", "headline": plain(problem or name)[:110],
           "description": plain(FL(c, "Ringkasan", lang)), "image": abs_url(img), "inLanguage": HTML_LANG[lang],
           "author": {"@type": "Organization", "name": NAMA}, "publisher": {"@type": "Organization", "name": NAMA, "logo": {"@type": "ImageObject", "url": abs_url(LOGO)}},
           "mainEntityOfPage": abs_url(path)}
    title = f'{T("label.studi", lang)}: {name} | {NAMA}'
    emit(path, lang, alts, shell(lang, path, alts, title, FL(c, "Ringkasan", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path), art], crumbs=crumbs, og_image=img, og_type="article"))


# ---------------------------------------------------------------------------
# Halaman: Blog (hub + artikel)
# ---------------------------------------------------------------------------
def page_blog_hub(lang):
    alts = {l: route("blog", l) for l in LANGS}
    path = alts[lang]
    arts = [a for a in ARTIKEL if path_artikel(a, lang)]
    grid = "".join(card_artikel(a, lang) for a in arts) or f'<p class="muted">{esc(T("blog.kosong", lang))}</p>'
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.blog", lang), None)]
    body = f"""<section class="page-hero wide"><div class="container narrow"><h1>{hl(T("blog.h1", lang))}</h1><p class="lead">{esc(T("blog.sub", lang))}</p></div></section>
<section class="section pt0"><div class="container"><div class="case-grid">{grid}</div></div></section>
{newsletter(lang, "Blog" if lang == "id" else "Blog (EN)")}"""
    emit(path, lang, alts, shell(lang, path, alts, T("blog.title", lang), T("blog.meta", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path)], crumbs=crumbs))


def fmt_date(d, lang):
    if not d:
        return ""
    try:
        y, m, dd = [int(x) for x in d[:10].split("-")]
    except ValueError:
        return d
    bulan = {"id": ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
             "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
    return f"{dd} {bulan[lang][m - 1]} {y}" if lang == "id" else f"{bulan[lang][m - 1]} {dd}, {y}"


def page_artikel(a, lang):
    path = path_artikel(a, lang)
    if not path:
        return
    alts = {l: path_artikel(a, l) for l in LANGS}
    title = FL(a, "Judul", lang)
    rel = [m for m in links(a, "Halaman Solusi") if path_masalah(m, lang)]
    rel_html = "".join(card_masalah(m, lang) for m in rel)
    more = [x for x in ARTIKEL if x["id"] != a["id"] and path_artikel(x, lang)][:3]
    tanggal = F(a, "Tanggal Terbit", "")
    img = localize_attachment(a, "Gambar Cover", "")
    crumbs = [(T("crumb.home", lang), route("home", lang)), (T("nav.blog", lang), route("blog", lang)), (title, None)]
    body = f"""<section class="page-hero"><div class="container narrow">
  <span class="eyebrow">{esc(T("label.artikel", lang))}{(" · " + esc(fmt_date(tanggal, lang))) if tanggal else ""}</span>
  <h1>{esc(title)}</h1><p class="lead">{esc(FL(a, "Ringkasan", lang))}</p></div></section>
<section class="section pt0"><div class="container narrow">
  {f'<figure class="cover"><img src="{u(img)}" alt="" width="1200" height="660"></figure>' if img else ""}
  <article class="prose">{md_to_html(FL(a, "Isi", lang))}</article>
</div></section>
{f'<section class="section tint"><div class="container">{section_head(T("nav.solusi", lang), T("blog.terkait", lang))}<div class="problem-grid">{rel_html}</div></div></section>' if rel_html else ""}
{cta_band(lang)}
{f'<section class="section"><div class="container">{section_head(T("nav.blog", lang), T("blog.kembali", lang))}<div class="case-grid">{"".join(card_artikel(x, lang) for x in more)}</div></div></section>' if more else ""}"""
    art = {"@context": "https://schema.org", "@type": "Article", "headline": plain(title)[:110],
           "description": plain(FL(a, "Ringkasan", lang)), "inLanguage": HTML_LANG[lang],
           "image": abs_url(img or OG_IMAGE),
           "author": {"@type": "Organization", "name": NAMA},
           "publisher": {"@type": "Organization", "name": NAMA, "logo": {"@type": "ImageObject", "url": abs_url(LOGO)}},
           "mainEntityOfPage": abs_url(path)}
    if tanggal:
        art["datePublished"] = tanggal
    emit(path, lang, alts, shell(lang, path, alts, f"{title} | {NAMA}", FL(a, "Ringkasan", lang), body,
                                 schemas=[breadcrumb_schema(crumbs, lang, path), art], crumbs=crumbs, og_image=img or None, og_type="article"))


# ---------------------------------------------------------------------------
# 404, redirect lama, sitemap, robots, aset
# ---------------------------------------------------------------------------
def page_404():
    lang = "id"
    alts = {"id": route("home", "id"), "en": route("home", "en")}
    body = f"""<section class="page-hero"><div class="container narrow center">
  <h1>{esc(T("nf.title", "id"))}</h1><p class="lead">{esc(T("nf.p", "id"))}</p>
  <p class="lead" lang="en">{esc(T("nf.p", "en"))}</p>
  <div class="btn-row center-row"><a class="btn btn-primary" href="{u(route("solusi", "id"))}">{esc(T("nf.btn", "id"))}</a>
  <a class="btn btn-ghost" href="{u(route("solusi", "en"))}">{esc(T("nf.btn", "en"))}</a></div>
</div></section>"""
    write_file("404.html", shell(lang, "/404.html", alts, f'{T("nf.title", "id")} | {NAMA}', T("nf.p", "id"), body, noindex=True))


def legacy_redirects():
    for old, new in LEGACY_REDIRECTS.items():
        target = u(new)
        html = f"""<!DOCTYPE html><html lang="id"><head><meta charset="UTF-8">
<title>{esc(NAMA)}</title><meta name="robots" content="noindex,follow">
<link rel="canonical" href="{abs_url(new)}"><meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(target)} + location.hash);</script></head>
<body><p>Halaman ini sudah pindah ke <a href="{target}">{abs_url(new)}</a>.</p></body></html>"""
        write_file(old, html)


def sitemap_and_robots():
    today = date.today().isoformat()
    entries = []
    for path, alts in SITEMAP:
        alt = ""
        if alts.get("id") and alts.get("en"):
            alt = (f'\n    <xhtml:link rel="alternate" hreflang="id" href="{abs_url(alts["id"])}"/>'
                   f'\n    <xhtml:link rel="alternate" hreflang="en" href="{abs_url(alts["en"])}"/>'
                   f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{abs_url(alts["id"])}"/>')
        entries.append(f"  <url>\n    <loc>{abs_url(path)}</loc>\n    <lastmod>{today}</lastmod>{alt}\n  </url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(entries) + "\n</urlset>\n")
    write_file("sitemap.xml", xml)
    write_file("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")


def write_assets():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("site.css", "site.js"):
        with open(os.path.join(here, "assets_src", name), encoding="utf-8") as f:
            write_file(f"assets/{name}", f.read())
    write_file(".nojekyll", "")


def cleanup_stale():
    """Hapus file yang dulu dibuat script ini tapi sekarang tidak lagi dibuat."""
    mpath = os.path.join(REPO_ROOT, MANIFEST)
    old = []
    if os.path.exists(mpath):
        try:
            with open(mpath, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:
            old = []
    for rel in old:
        if rel in GENERATED or rel in LEGACY_REDIRECTS or ".." in rel:
            continue
        full = os.path.join(REPO_ROOT, rel)
        if os.path.isfile(full):
            os.remove(full)
            print("  - hapus", rel)
            d = os.path.dirname(full)
            while d != REPO_ROOT and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
                d = os.path.dirname(d)
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(sorted(GENERATED), f, indent=0)


def css_version():
    here = os.path.dirname(os.path.abspath(__file__))
    import hashlib
    h = hashlib.md5()
    for name in ("site.css", "site.js"):
        with open(os.path.join(here, "assets_src", name), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:8]


CSS_VERSION = css_version()


def main():
    write_assets()
    for lang in LANGS:
        page_home(lang)
        page_solusi_hub(lang)
        for m in MASALAH:
            page_masalah(m, lang)
        page_untuk_hub(lang)
        for a in AUDIENS:
            page_audiens(a, lang)
        page_studi_hub(lang)
        for c in STUDI:
            page_studi(c, lang)
        page_blog_hub(lang)
        for a in ARTIKEL:
            page_artikel(a, lang)
    page_404()
    legacy_redirects()
    sitemap_and_robots()
    cleanup_stale()
    print(f"Selesai: {len(SITEMAP)} halaman ({len(MASALAH)} masalah bisnis, {len(AUDIENS)} audiens, "
          f"{len(STUDI)} studi kasus, {len(ARTIKEL)} artikel) x 2 bahasa + {len(LEGACY_REDIRECTS)} pengalihan URL lama.")


if __name__ == "__main__":
    main()
