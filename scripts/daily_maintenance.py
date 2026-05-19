#!/usr/bin/env python3
"""Daily Maintenance Script — Salut Etam Betuah"""

import anthropic, requests, datetime, json, os, re, sys

TODAY     = datetime.date.today()
TODAY_ISO = TODAY.strftime("%Y-%m-%d")
BULAN     = {1:"Januari",2:"Februari",3:"Maret",4:"April",5:"Mei",6:"Juni",
             7:"Juli",8:"Agustus",9:"September",10:"Oktober",11:"November",12:"Desember"}
TODAY_ID  = f"{TODAY.day} {BULAN[TODAY.month]} {TODAY.year}"
DAY_NAME  = TODAY.strftime("%A").replace(
    "Monday","Senin").replace("Tuesday","Selasa").replace(
    "Wednesday","Rabu").replace("Thursday","Kamis").replace(
    "Friday","Jumat").replace("Saturday","Sabtu").replace("Sunday","Minggu")

SERVICE_AREA = "Samarinda, Balikpapan, Kutai Kartanegara, Bontang, Berau, dan seluruh Kalimantan Timur, serta seluruh Indonesia"

TEMA = {
    "Senin":  "semangat awal minggu, info pendaftaran, motivasi kuliah sambil kerja",
    "Selasa": "info layanan, cerita dari mahasiswa berbagai kota Kaltim",
    "Rabu":   "tips kuliah UT, info RPL untuk ASN dan karyawan",
    "Kamis":  "info akademik, registrasi, ujian, deadline",
    "Jumat":  "cerita sukses, motivasi akhir pekan",
    "Sabtu":  "reminder jam buka, suasana kantor"
}.get(DAY_NAME, "info layanan UT")

print(f"📅 {DAY_NAME}, {TODAY_ID}")

# ── STEP 1: Fetch 5-star reviews ──────────────────────────────
api_key  = os.environ.get("GOOGLE_PLACES_API_KEY", "")
place_id = os.environ.get("GOOGLE_PLACE_ID", "")
reviews  = []

if api_key and place_id:
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": place_id, "fields": "reviews",
                    "language": "id", "reviews_sort": "newest", "key": api_key},
            timeout=10
        )
        data = resp.json()
        if data.get("status") == "OK":
            all_r = data.get("result", {}).get("reviews", [])
            GRADS = ["from-blue-500 to-blue-700","from-amber-500 to-orange-600",
                     "from-emerald-500 to-teal-600","from-purple-500 to-indigo-600",
                     "from-rose-500 to-pink-600","from-cyan-500 to-blue-600"]
            for i, r in enumerate(all_r):
                if r.get("rating") != 5: continue
                text = r.get("text","").strip()
                if len(text) < 20: continue
                author = r.get("author_name","Anonim")
                parts  = author.strip().split()
                initials = (parts[0][0] + (parts[1][0] if len(parts)>1 else parts[0][-1])).upper()
                reviews.append({
                    "author":   author,
                    "initials": initials,
                    "text":     text[:280]+("..." if len(text)>280 else ""),
                    "time":     r.get("relative_time_description",""),
                    "gradient": GRADS[len(reviews) % len(GRADS)]
                })
            print(f"✅ {len(reviews)} ulasan bintang 5 diambil")
        else:
            print(f"⚠️  Google API: {data.get('status')}")
    except Exception as e:
        print(f"⚠️  Google API error: {e}")
else:
    print("ℹ️  Google secrets tidak diset — skip review sync")

# ── STEP 2: Update testimoni di index.html ────────────────────
if reviews and os.path.exists("index.html"):
    def esc(t):
        return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def build(r):
        return (f'        <div class="testi-item shadow-card">\n'
                f'          <div class="flex items-center gap-3 mb-4">\n'
                f'            <div class="w-10 h-10 rounded-full bg-gradient-to-br {r["gradient"]} '
                f'flex items-center justify-center text-sm font-bold text-white flex-shrink-0">'
                f'{esc(r["initials"])}</div>\n'
                f'            <div><div class="text-sm font-bold text-brand-navy">{esc(r["author"])}</div>'
                f'<div class="text-[10px] text-slate-400">Google Maps · {esc(r["time"])}</div></div>\n'
                f'            <div class="ml-auto flex text-amber-400 text-sm">★★★★★</div>\n'
                f'          </div>\n'
                f'          <p class="text-xs text-slate-600 leading-relaxed">"{esc(r["text"])}"</p>\n'
                f'        </div>')

    new_track = ('<div class="testi-track" id="testi-track">\n' +
                 "\n".join(build(r) for r in reviews[:6]) +
                 '\n      </div>')

    with open("index.html","r",encoding="utf-8") as f:
        html = f.read()

    si = html.find('<div class="testi-track" id="testi-track">')
    if si != -1:
        pos, depth = si, 0
        while pos < len(html):
            if html[pos:pos+4] == "<div": depth += 1
            elif html[pos:pos+6] == "</div>":
                depth -= 1
                if depth == 0: ei = pos+6; break
            pos += 1
        html = html[:si] + new_track + html[ei:]
        with open("index.html","w",encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Testimoni diperbarui: {len(reviews[:6])} ulasan bintang 5")
    else:
        print("⚠️  testi-track tidak ditemukan")

# ── STEP 3: Generate GBP content dengan AI ───────────────────
anthropic_key = os.environ.get("ANTHROPIC_API_KEY","")
if not anthropic_key:
    print("⚠️  ANTHROPIC_API_KEY tidak diset — skip GBP generation")
    sys.exit(0)

client = anthropic.Anthropic(api_key=anthropic_key)

def call_ai(prompt, max_tokens=1200):
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role":"user","content":prompt}]
    )
    raw = resp.content[0].text.strip()
    for m in ["```json","```"]:
        if m in raw:
            raw = raw.split(m)[1].split("```")[0].strip()
            break
    return json.loads(raw)

posts = call_ai(
    f"Buat 2 caption Google Business Profile untuk Salut Etam Betuah "
    f"yang melayani {SERVICE_AREA}.\n\n"
    f"ATURAN KETAT: Jangan sebut 'tim kami'/'admin kami'/'kami siap'. "
    f"Jangan gaya korporat. Tulis seperti orang Samarinda share info ke teman. "
    f"Sesekali sebut kota lain (Balikpapan, Bontang dll). Max 220 karakter per post. "
    f"1-2 emoji saja.\n\nHari ini: {DAY_NAME}, {TODAY_ID}. Tema: {TEMA}\n\n"
    f'Return JSON: {{"post_1":{{"konten":"...","topik":"..."}},'
    f'"post_2":{{"konten":"...","topik":"..."}}}}\nReturn HANYA JSON valid.'
)
print("✅ Google Posts generated")

review_tmpl = call_ai(
    f"Buat template untuk Salut Etam Betuah yang melayani {SERVICE_AREA}.\n\n"
    f"ATURAN REPLY BINTANG 5: Formal dan profesional. Boleh mulai "
    f"'Terima kasih banyak...' atau 'Alhamdulillah...'. Hangat tapi sopan. Max 180 karakter.\n\n"
    f"ATURAN CONTOH REVIEW: Dari sudut pandang MAHASISWA sungguhan. Informal, "
    f"ada pengalaman nyata. Sebut 'Salut Etam Betuah' dan kota secara natural. "
    f"BUKAN 'Pelayanan sangat memuaskan dan profesional'.\n\n"
    f"ATURAN TEMPLATE MINTA REVIEW: Pesan WA singkat personal. "
    f"Sertakan link: https://g.page/r/CcXrBsm7Ua8xEAE/review\n\n"
    f'Return JSON: {{"template_wa":"...","contoh_1":"...","contoh_2":"...",'
    f'"contoh_3":"...","reply_bintang5":"...","reply_rendah":"..."}}\nReturn HANYA JSON valid.'
)
print("✅ Review templates generated")

def s(v, d=""): return str(v) if v else d

md = f"""# Konten GBP — Salut Etam Betuah
### {DAY_NAME}, {TODAY_ID}
*Melayani: {SERVICE_AREA}*

---

## Google Posts Hari Ini

### Post 1 — {s(posts.get("post_1",{}).get("topik",""))}
> GBP → Tambahkan pembaruan → salin teks → tombol "Pelajari selengkapnya" → salutetambetuah.id

```
{s(posts.get("post_1",{}).get("konten",""))}
```
*{len(s(posts.get("post_1",{}).get("konten","")))} karakter*

---

### Post 2 — {s(posts.get("post_2",{}).get("topik",""))}
```
{s(posts.get("post_2",{}).get("konten",""))}
```
*{len(s(posts.get("post_2",{}).get("konten","")))} karakter*

---

## Minta Review dari Mahasiswa

### Pesan WhatsApp
*Ganti [Nama] sebelum kirim. Kirim ke 2-3 mahasiswa yang baru selesai urusan.*

```
{s(review_tmpl.get("template_wa",""))}
```

### Contoh Teks Review (dari sudut pandang mahasiswa — natural, bukan promosi)

**Mahasiswa Samarinda:**
```
{s(review_tmpl.get("contoh_1",""))}
```

**Mahasiswa luar kota (Balikpapan / Bontang / Berau / Kukar):**
```
{s(review_tmpl.get("contoh_2",""))}
```

**ASN / Karyawan / RPL:**
```
{s(review_tmpl.get("contoh_3",""))}
```

---

## Reply Ulasan di Google Maps

**Untuk ulasan ★★★★★ — formal & profesional:**
```
{s(review_tmpl.get("reply_bintang5",""))}
```

**Untuk ulasan bintang rendah / keluhan:**
```
{s(review_tmpl.get("reply_rendah",""))}
```

---

## Area Layanan
Salut Etam Betuah melayani mahasiswa UT dari:
**Samarinda · Balikpapan · Kutai Kartanegara · Bontang · Berau**
dan seluruh Kalimantan Timur, serta **seluruh Indonesia**

Konsultasi: WA 0822-5063-8289 (24 jam) | salutetambetuah.id

---
*Update: {TODAY_ID} | Auto-generated by GitHub Actions + Anthropic AI*
"""

with open("GBP_KONTEN_SALUT.md","w",encoding="utf-8") as f:
    f.write(md)
print("✅ GBP_KONTEN_SALUT.md selesai")
