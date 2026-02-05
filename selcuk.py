import re
import os
import shutil
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0"}

def find_active_domain(start=1825, end=1880):
    for i in range(start, end+1):
        url = f"https://www.selcuksportshd{i}.xyz/"
        try:
            req = Request(url, headers=headers)
            html = urlopen(req, timeout=5).read().decode()
            if "uxsyplayer" in html:
                print(f"✅ Aktif domain bulundu: {url}")
                return url, html
        except:
            continue
    return None, None

def get_player_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", attrs={"data-url": True}):
        data_url = a["data-url"].strip()
        if data_url.startswith("/"):
            data_url = "https://" + data_url.lstrip("/")
        name = a.text.strip()
        if not name:
            name = data_url.split("id=")[-1] if "id=" in data_url else "Kanal"
        links.append({"url": data_url, "name": name})
    return links

def get_m3u8_url(player_url, referer):
    try:
        req = Request(player_url, headers={"User-Agent": headers["User-Agent"], "Referer": referer})
        html = urlopen(req, timeout=10).read().decode()
        patterns = [
            r'this\.baseStreamUrl\s*=\s*"([^"]+)"',
            r"this\.baseStreamUrl\s*=\s*'([^']+)'",
            r'baseStreamUrl\s*:\s*"([^"]+)"',
            r"baseStreamUrl\s*:\s*'([^']+)'"
        ]
        base_url = None
        for p in patterns:
            m = re.search(p, html)
            if m:
                base_url = m.group(1)
                break
        if not base_url: return None
        m_id = re.search(r"id=([a-zA-Z0-9]+)", player_url)
        if not m_id: return None
        stream_id = m_id.group(1)
        if not base_url.endswith("/"): base_url += "/"
        return f"{base_url}{stream_id}/playlist.m3u8"
    except:
        return None

def slugify(name):
    """Dosya adı için ismi temizler"""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()

def create_individual_files(output_folder="selcuk"):
    print("🔍 Domain aranıyor...")
    domain, html = find_active_domain()
    if not html:
        print("❌ Çalışan domain bulunamadı!")
        return

    # Klasörü hazırla (varsa önce siler temiz bir liste yapar)
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    players = get_player_links(html)
    if not players: return

    print(f"📺 {len(players)} kanal işleniyor...\n")
    ok = 0

    for ch in players:
        m3u8_link = get_m3u8_url(ch["url"], domain)
        if m3u8_link:
            file_name = f"{slugify(ch['name'])}.m3u8"
            file_path = os.path.join(output_folder, file_name)
            
            # M3U8 içeriğini oluştur (VLC ve Player uyumlu)
            content = [
                "#EXTM3U",
                f"#EXTINF:-1,{ch['name']}",
                f"#EXTVLCOPT:http-referrer={domain}",
                f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}",
                m3u8_link
            ]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            
            print(f"✅ Oluşturuldu: {file_name}")
            ok += 1
        else:
            print(f"❌ Atlandı: {ch['name']}")

    print(f"\n🚀 İşlem Tamamlandı! {ok} dosya '{output_folder}' klasörüne kaydedildi.")

if __name__ == "__main__":
    create_individual_files()
