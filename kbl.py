import requests
import json
import gzip
import os
from io import BytesIO

# --- YOUTUBE FORMATI OLUŞTURUCU FONKSİYON ---
def get_youtube_style_raw(master_url, auth_headers):
    """Master URL'ye gider, içindeki tüm kaliteleri ayıklar ve tam linkleri dizer."""
    try:
        # KabloWeb'in master playlistini indiriyoruz
        r = requests.get(master_url, headers=auth_headers, timeout=10)
        if r.status_code != 200:
            return f"#EXTM3U\n{master_url}"
            
        lines = r.text.splitlines()
        output = ["#EXTM3U"]
        
        # Base URL'yi alıyoruz (Eksik linkleri tamamlamak için)
        # Örn: https://ottcdn.../24tv/ -> bu kısmını ayırır
        base_url = master_url.rsplit('/', 1)[0]
        
        for i in range(len(lines)):
            # Eğer satır kalite bilgisi içeriyorsa (BANDWIDTH, RESOLUTION vb.)
            if "#EXT-X-STREAM-INF" in lines[i]:
                output.append(lines[i]) # Bilgi satırını ekle
                
                # Bir sonraki satırdaki linki al ve tam linke çevir
                next_line = lines[i+1].strip()
                if not next_line.startswith("http"):
                    full_link = f"{base_url}/{next_line}"
                else:
                    full_link = next_line
                
                output.append(full_link) # Tam linki ekle
                
        return "\n".join(output)
    except:
        return f"#EXTM3U\n{master_url}"

# --- ANA KODUN (GELİŞTİRİLMİŞ HALİ) ---
def get_canli_tv_m3u():
    url = "https://core-api.kablowebtv.com/api/channels"
    save_folder = "kablo"
    
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://tvheryerde.com",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"
    }

    try:
        print("📡 API'den kanallar çekiliyor...")
        response = requests.get(url, headers=headers, params={"checkip": "false"}, timeout=30)
        
        # Gzip açma işlemi
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')
        
        data = json.loads(content)
        channels = data['Data']['AllChannels']

        for channel in channels:
            name = channel.get('Name')
            hls_url = channel.get('StreamData', {}).get('HlsStreamUrl')
            
            if not name or not hls_url: continue
            if channel.get('Categories') and channel['Categories'][0].get('Name') == "Bilgilendirme": continue

            print(f"🎬 {name} için Raw oluşturuluyor...")
            
            # --- İŞTE BURASI: YouTube Formatını üretiyoruz ---
            youtube_format_content = get_youtube_style_raw(hls_url, headers)
            
            # Dosyaya yazma
            file_name = name.replace(" ", "_").replace("/", "-") + ".m3u8"
            with open(os.path.join(save_folder, file_name), "w", encoding="utf-8") as f:
                f.write(youtube_format_content)

        print(f"\n✅ İşlem başarılı! 'kablo' klasöründeki her m3u8 artık istediğin formatta.")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    get_canli_tv_m3u()
