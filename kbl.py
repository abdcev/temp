import requests
import json
import gzip
import os
import re
from io import BytesIO

def get_youtube_style_content(master_url, headers):
    """KabloWebTV ana linkine girer ve YouTube formatında (INF + Link) içerik döner."""
    try:
        r = requests.get(master_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return f"#EXTM3U\n#EXT-X-VERSION:3\n{master_url}"
            
        lines = r.text.splitlines()
        output = ["#EXTM3U", "#EXT-X-VERSION:3"]
        
        for i in range(len(lines)):
            if "#EXT-X-STREAM-INF" in lines[i]:
                inf_line = lines[i]
                url_line = lines[i+1].strip() if i+1 < len(lines) else ""
                
                if url_line:
                    # Link tam değilse (relative ise) tamamla
                    if not url_line.startswith("http"):
                        base = master_url.rsplit('/', 1)[0]
                        full_url = f"{base}/{url_line}"
                    else:
                        full_url = url_line
                    
                    output.append(inf_line)
                    output.append(full_url)
        return "\n".join(output)
    except:
        return f"#EXTM3U\n#EXT-X-VERSION:3\n{master_url}"

def get_canli_tv_m3u():
    url = "https://core-api.kablowebtv.com/api/channels"
    save_folder = "kanallar" # Her kanalın RAW dosyası burada olacak
    
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"
    }

    params = {"checkip": "false"}
    
    try:
        print("📡 CanliTV API'den veri alınıyor...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')
        
        data = json.loads(content)
        channels = data['Data']['AllChannels']
        
        with open("kbl.m3u", "w", encoding="utf-8") as main_m3u:
            main_m3u.write("#EXTM3U\n")
            
            for channel in channels:
                name = channel.get('Name')
                hls_url = channel.get('StreamData', {}).get('HlsStreamUrl')
                logo = channel.get('PrimaryLogoImageUrl', '')
                categories = channel.get('Categories', [])
                
                if not name or not hls_url or (categories and categories[0].get('Name') == "Bilgilendirme"):
                    continue

                # 1. YouTube Tarzı İçeriği Al (Kaliteleri Aç)
                print(f"⚙️ İşleniyor: {name}")
                raw_content = get_youtube_style_content(hls_url, headers)
                
                # 2. Kanalı Dosyaya Kaydet (RAW oluşturma)
                file_safe_name = name.replace(" ", "_").replace("/", "-")
                file_path = os.path.join(save_folder, f"{file_safe_name}.m3u8")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(raw_content)

                # 3. Ana M3U dosyasına GitHub linkini veya yerel yolu ekle
                group = categories[0].get('Name', 'Genel') if categories else 'Genel'
                main_m3u.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n')
                # Buraya GitHub linkini gelecekte otomatik ekleyebilirsin
                main_m3u.write(f'kanallar/{file_safe_name}.m3u8\n')

        print(f"✅ Bitti! 'kanallar' klasöründe her kanalın içindeki linkler YouTube formatına çevrildi.")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    get_canli_tv_m3u()
