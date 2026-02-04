import requests
import re
import os
import json

# --- AYARLAR ---
# Buraya kendi API bilgilerini gir
API_URL = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE" 
SAVE_FOLDER = "kanallar" # Dosyaların kaydedileceği klasör

# Klasör yoksa oluştur
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

def get_youtube_style_m3u8(master_url):
    """
    KabloWebTV master linkini alır, tüm alt kaliteleri bulur
    ve YouTube'un Raw formatında (tüm varyantlar alt alta) döner.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(master_url, timeout=15, headers=headers)
        if r.status_code != 200:
            return f"#EXTM3U\n#EXT-X-VERSION:3\n{master_url}"
            
        lines = r.text.splitlines()
        # Başlangıç satırlarını oluştur
        output = ["#EXTM3U", "#EXT-X-VERSION:3"]
        
        # Kaliteleri ayıkla ve listele
        for i in range(len(lines)):
            if "#EXT-X-STREAM-INF" in lines[i]:
                inf_line = lines[i]
                url_line = lines[i+1].strip() if i+1 < len(lines) else ""
                
                if url_line:
                    # Göreceli linki tam linke çevir (Örn: tracks-v1... -> https://ottcdn...)
                    if not url_line.startswith("http"):
                        base = master_url.rsplit('/', 1)[0]
                        full_url = f"{base}/{url_line}"
                    else:
                        full_url = url_line
                    
                    # Format: Önce Bilgi Satırı, sonra Tam URL
                    output.append(inf_line)
                    output.append(full_url)

        return "\n".join(output)
        
    except Exception as e:
        print(f"❌ Hata (Varyant çekilemedi): {e}")
        return f"#EXTM3U\n#EXT-X-VERSION:3\n{master_url}"

def main():
    print("🚀 KabloWebTV Kanalları Çekiliyor...")
    
    try:
        # 1. Ana API'den kanal listesini çek
        response = requests.get(API_URL, timeout=20)
        data = response.json()
        
        # API yapına göre burayı güncelle (Örn: data['channels'] gibi)
        channels = data if isinstance(data, list) else data.get('channels', [])

        for channel in channels:
            name = channel.get('Name', 'Bilinmeyen_Kanal').replace(" ", "_").replace("/", "-")
            hls_url = channel.get('StreamData', {}).get('HlsStreamUrl')
            
            if hls_url:
                print(f"📡 İşleniyor: {name}")
                
                # YouTube formatındaki m3u8 içeriğini hazırla
                final_m3u8 = get_youtube_style_m3u8(hls_url)
                
                # Dosya adını belirle ve kaydet
                file_name = f"{name}.m3u8"
                file_path = os.path.join(SAVE_FOLDER, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(final_m3u8)
                
                print(f"✅ Kaydedildi: {file_name}")
            else:
                print(f"⚠️ Atlandı (URL yok): {name}")

        print("\n✨ Tüm kanallar YouTube formatında hazırlandı!")

    except Exception as e:
        print(f"💥 Ana döngü hatası: {e}")

if __name__ == "__main__":
    main()
