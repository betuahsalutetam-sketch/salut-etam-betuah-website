#!/usr/bin/env python3
"""Weekly SEO Audit — Salut Etam Betuah"""

import anthropic, datetime, json, os, re

TODAY    = datetime.date.today()
TODAY_ID = TODAY.strftime("%Y-%m-%d")
BULAN    = {1:"Januari",2:"Februari",3:"Maret",4:"April",5:"Mei",6:"Juni",
            7:"Juli",8:"Agustus",9:"September",10:"Oktober",11:"November",12:"Desember"}
TODAY_FULL = f"{TODAY.day} {BULAN[TODAY.month]} {TODAY.year}"

print(f"🔍 Weekly SEO Audit — {TODAY_FULL}")

anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not anthropic_key:
    print("⚠️  ANTHROPIC_API_KEY tidak diset — skip audit")
    exit(0)

client = anthropic.Anthropic(api_key=anthropic_key)

# ── Baca index.html ───────────────────────────────────────────
html_content = ""
if os.path.exists("index.html"):
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    print(f"✅ index.html dibaca: {len(html_content):,} karakter")
else:
    print("⚠️  index.html tidak ditemukan")

# ── Ambil meta tags dari HTML ─────────────────────────────────
def extract_meta(html, name):
    m = re.search(rf'<meta[^>]+name=["\']?{name}["\']?[^>]+content=["\']([^"\']+)["\']', html, re.I)
    if not m:
        m = re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']?{name}["\']?', html, re.I)
    return m.group(1)[:120] if m else "(tidak ditemukan)"

title_m  = re.search(r"<title>([^<]+)</title>", html_content, re.I)
title    = title_m.group(1)[:100] if title_m else "(tidak ditemukan)"
desc     = extract_meta(html_content, "description")
keywords = extract_meta(html_content, "keywords")

print(f"📌 Title   : {title}")
print(f"📌 Desc    : {desc[:80]}...")
print(f"📌 Keywords: {keywords[:80]}...")

# ── AI Audit ──────────────────────────────────────────────────
snippet = html_content[:6000] if html_content else "index.html tidak tersedia"

prompt = f"""Kamu adalah SEO auditor untuk website Salut Etam Betuah (salutetambetuah.id).
Ini adalah sentra layanan Universitas Terbuka #1 di Samarinda, melayani seluruh Kalimantan Timur dan Indonesia.

Data hari ini ({TODAY_FULL}):
- Title tag: {title}
- Meta description: {desc}
- Keywords: {keywords}

Penggalan HTML (index.html):
{snippet[:4000]}

Berikan audit SEO mingguan dalam format JSON berikut.
Return HANYA JSON valid, tanpa teks lain:

{{
  "skor_seo": 85,
  "ringkasan": "Ringkasan kondisi SEO 2-3 kalimat",
  "kekuatan": ["kekuatan 1", "kekuatan 2", "kekuatan 3"],
  "masalah": [
    {{"prioritas": "tinggi", "masalah": "...", "solusi": "..."}},
    {{"prioritas": "sedang", "masalah": "...", "solusi": "..."}}
  ],
  "rekomendasi_konten": ["rekomendasi 1", "rekomendasi 2"],
  "keyword_target": ["keyword utama 1", "keyword utama 2", "keyword utama 3"],
  "action_minggu_ini": ["aksi 1", "aksi 2", "aksi 3"]
}}"""

try:
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip()
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0].strip()
            break
    audit = json.loads(raw)
    print(f"✅ AI Audit selesai — Skor SEO: {audit.get('skor_seo', '?')}/100")
except Exception as e:
    print(f"⚠️  AI audit error: {e}")
    audit = {"skor_seo": 0, "ringkasan": "Audit gagal", "kekuatan": [],
             "masalah": [], "rekomendasi_konten": [], "keyword_target": [],
             "action_minggu_ini": []}

# ── Tulis laporan ─────────────────────────────────────────────
def li(items):
    return "\n".join(f"- {i}" for i in items) if items else "- (tidak ada)"

def li_masalah(items):
    if not items: return "- (tidak ada masalah ditemukan)"
    return "\n".join(
        f"- [{m.get('prioritas','?').upper()}] {m.get('masalah','')} → {m.get('solusi','')}"
        for m in items
    )

laporan = f"""# Laporan SEO Mingguan — Salut Etam Betuah
### {TODAY_FULL} | salutetambetuah.id

---

## Skor SEO: {audit.get('skor_seo', 0)}/100

{audit.get('ringkasan', '')}

---

## Kekuatan
{li(audit.get('kekuatan', []))}

---

## Masalah & Solusi
{li_masalah(audit.get('masalah', []))}

---

## Rekomendasi Konten Minggu Ini
{li(audit.get('rekomendasi_konten', []))}

---

## Keyword Target
{li(audit.get('keyword_target', []))}

---

## Action Items Minggu Ini
{li(audit.get('action_minggu_ini', []))}

---

## Data Teknis
- Title: `{title}`
- Meta description: `{desc[:100]}`
- Keywords: `{keywords[:100]}`

---
*Dibuat otomatis: {TODAY_FULL} | GitHub Actions + Anthropic AI*
"""

report_file = f"SEO_AUDIT_{TODAY_ID}.md"
with open(report_file, "w", encoding="utf-8") as f:
    f.write(laporan)
print(f"✅ Laporan disimpan: {report_file}")

# ── Update MAINTENANCE_LOG ────────────────────────────────────
if os.path.exists("MAINTENANCE_LOG.md"):
    with open("MAINTENANCE_LOG.md", "a", encoding="utf-8") as f:
        f.write(f"\n## Weekly Audit {TODAY_ID}\n")
        f.write(f"- Skor SEO: {audit.get('skor_seo', 0)}/100\n")
        f.write(f"- {len(audit.get('masalah', []))} masalah ditemukan\n")
        f.write(f"- Laporan: {report_file}\n")
    print("✅ MAINTENANCE_LOG diperbarui")

print("🎉 Weekly SEO Audit selesai!")
