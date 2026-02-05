import requests
import re
import os

START_URL = "https://url24.link/AtomSporTV"
SAVE_FOLDER = "rnl"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://url24.link/'
}

# ---------------- UTILS ----------------
def slugify(name):
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()

# ---------------- DOMAIN ----------------
def get_base_domain():
    try:
        r1 = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in r1.headers:
            r2 = requests.get(r1.headers['location'], headers=headers, allow_redirects=False, timeout=10)
            if 'location' in r2.headers:
                return r2.headers['location'].rstrip('/')
    except:
        pass
    return "https://www.atomsportv480.top"

# ---------------- STREAM ----------------
def get_channel_m3u8(channel_id, base_domain):
    try:
        r = requests.get(f"{base_domain}/matches?id={channel_id}", headers=headers, timeout=10)
        html = r.text

        m = re.search(r'fetch\(["\'](.*?)["\']', html)
        if not m:
            return None

        fetch_url = m.group(1)
        if not fetch_url.endswith(channel_id):
            fetch_url += channel_id

        h = headers.copy()
        h["Origin"] = base_domain
        h["Referer"] = base_domain

        r2 = requests.get(fetch_url, headers=h, timeout=10)
        data = r2.text

        m3u = re.search(r'"deismackanal":"(.*?)"', data) or \
              re.search(r'"(?:stream|url|source)":\s*"(.*?\.m3u8)"', data)

        return m3u.group(1).replace("\\", "") if m3u else None
    except:
        return None

# ---------------- CHANNEL LIST ----------------
def get_tv_channels():
    return [
        ("bein-sports-1", "BEIN SPORTS 1"),
        ("bein-sports-2", "BEIN SPORTS 2"),
        ("bein-sports-3", "BEIN SPORTS 3"),
        ("bein-sports-4", "BEIN SPORTS 4"),
        ("bein-sports-6", "BEIN SPORTS 5"),
        ("bein-sports-max-1", "BEIN SPORTS MAX 1"),
        ("bein-sports-max-2", "BEIN SPORTS MAX 2"),
        ("s-sport", "S SPORT"),
        ("s-sport-2", "S SPORT 2"),
        ("tivibu-spor-1", "TİVİBU SPOR 1"),
        ("tivibu-spor-2", "TİVİBU SPOR 2"),
        ("tivibu-spor-3", "TİVİBU SPOR 3"),
        ("trt-spor", "TRT SPOR"),
        ("trt-yildiz", "TRT YILDIZ"),
        ("trt1", "TRT 1"),
        ("aspor", "ASPOR"),
    ]

# ---------------- MAIN ----------------
def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    base_domain = get_base_domain()
    channels = get_tv_channels()

    active_files = set()

    for cid, name in channels:
        slug = slugify(name)
        file_path = os.path.join(SAVE_FOLDER, f"{slug}.m3u8")

        m3u8 = get_channel_m3u8(cid, base_domain)

        if m3u8:
            content = "\n".join([
                "#EXTM3U",
                f"#EXTINF:-1,{name}",
                f"#EXTVLCOPT:http-referrer={base_domain}",
                f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}",
                m3u8
            ])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            active_files.add(file_path)
            print(f"✔ Güncellendi: {slug}.m3u8")
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✖ Silindi (offline): {slug}.m3u8")

    print("İşlem tamamlandı")

if __name__ == "__main__":
    main()
