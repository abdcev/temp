import requests
import json
import gzip
import os
import re
from io import BytesIO

# --- DOSYA ADI / ID TEMİZLEME FONKSİYONU ---
def slugify(name):
    """Kanal isimlerini dosya sistemine ve IPTV tvg-id için uygun hale getirir."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

# --- YOUTUBE/MASTER FORMATLI M3U8 ÇEKME ---
def get_youtube_style_raw(master_url, headers):
    """Master URL'deki tüm kalite linklerini toplar."""
    try:
        r = requests.get(master_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return f"#EXTM3U\n{master_url}"
            
        lines = r.text.splitlines()
        output = ["#EXTM3U"]
        
        base_url = master_url.rsplit('/', 1)[0]
        
        for i in range(len(lines)):
            if "#EXT-X-STREAM-INF" in lines[i]:
                output.append(lines[i])
                next_line = lines[i+1].strip()
                full_link = next_line if next_line.startswith("http") else f"{base_url}/{next_line}"
                output.append(full_link)
                
        return "\n".join(output)
    except:
        return f"#EXTM3U\n{master_url}"

# --- EPG XML ÇEKME ---
def get_epg_xml(headers, save_folder):
    url = "https://core-api.kablowebtv.com/api/epg"
    print("📺 EPG XML çekiliyor...")
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    try:
        with gzip.GzipFile(fileobj=BytesIO(r.content)) as gz:
            content = gz.read()
    except:
        content = r.content

    epg_path = os.path.join(save_folder, "epg.xml")
    with open(epg_path, "wb") as f:
        f.write(content)
    print("✅ EPG kaydedildi:", epg_path)

# --- ANA FONKSİYON ---
def get_canli_tv_m3u():
    url = "https://core-api.kablowebtv.com/api/channels"
    save_folder = "kablo"

    # --- KLASÖR KONTROLÜ ---
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"📂 '{save_folder}' klasörü oluşturuldu.")
    else:
        print(f"📂 '{save_folder}' klasörü mevcut, güncelleniyor...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://tvheryerde.com",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"
    }

    try:
        print("📡 API'den kanallar çekiliyor...")
        response = requests.get(url, headers=headers, params={"checkip": "false"}, timeout=30)
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)
        channels = data['Data']['AllChannels']

        playlist_path = os.path.join(save_folder, "playlist.m3u")
        with open(playlist_path, "w", encoding="utf-8") as playlist_file:
            playlist_file.write('#EXTM3U url-tvg="epg.xml"\n\n')

            ok = 0
            for channel in channels:
                name = channel.get('Name')
                hls_url = channel.get('StreamData', {}).get('HlsStreamUrl')
                logo = channel.get('LogoUrl', "")
                category = channel.get('Categories', [{}])[0].get('Name', "")

                if not name or not hls_url: 
                    continue
                if category == "Bilgilendirme": 
                    continue

                safe_name = slugify(name)
                extinf = f'#EXTINF:-1 tvg-id="{safe_name}" tvg-name="{name}" tvg-logo="{logo}" group-title="{category}",{name}'
                playlist_file.write(extinf + "\n")
                playlist_file.write(hls_url + "\n\n")
                ok += 1

        print(f"\n✅ {ok} kanal playlist.m3u içine kaydedildi.")
        # EPG XML çek
        get_epg_xml(headers, save_folder)

    except Exception as e:
        print(f"❌ Hata: {e}")

# --- SCRIPT ÇALIŞTIR ---
if __name__ == "__main__":
    get_canli_tv_m3u()
