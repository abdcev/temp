import requests
import json
import gzip
import os
import re
from io import BytesIO

def get_best_quality_url(master_url):
    """
    Master m3u8 içeriğini okur, BANDWIDTH değerlerini karşılaştırır 
    ve en yüksek bitrate'e sahip alt m3u8 linkini döner.
    """
    try:
        # User-agent eklemek önemli, bazen bot engeline takılabiliyor
        r = requests.get(master_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return master_url
            
        lines = r.text.splitlines()
        
        best_bandwidth = -1
        best_url = master_url
        
        for i in range(len(lines)):
            # #EXT-X-STREAM-INF satırında BANDWIDTH değerini ara
            if "#EXT-X-STREAM-INF" in lines[i]:
                match = re.search(r"BANDWIDTH=(\d+)", lines[i])
                if match:
                    current_bandwidth = int(match.group(1))
                    # Eğer mevcut bandwidth, bildiğimiz en iyisinden büyükse
                    if current_bandwidth > best_bandwidth:
                        best_bandwidth = current_bandwidth
                        # Bir sonraki satır linktir
                        potential_url = lines[i+1].strip()
                        
                        # Link tam URL mi yoksa göreceli mi kontrol et
                        if potential_url.startswith("http"):
                            best_url = potential_url
                        else:
                            # Göreceli link ise ana url'in base kısmıyla birleştir
                            base_path = master_url.rsplit('/', 1)[0]
                            best_url = f"{base_path}/{potential_url}"
        
        return best_url
    except Exception as e:
        print(f"⚠️ Kalite seçimi yapılamadı, orijinal link dönülüyor: {e}")
        return master_url

def create_separate_m3u8():
    # Buraya çalışan güncel token'ını yapıştır
    token = "eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE" 
    
    url = "https://core-api.kablowebtv.com/api/channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Authorization": f"Bearer {token}"
    }

    output_dir = "kanallar"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        print("🚀 Kanal listesi alınıyor...")
        response = requests.get(url, headers=headers, params={"checkip": "false"}, timeout=30)
        
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)
        channels = data.get('Data', {}).get('AllChannels', [])

        if not channels:
            print("❌ Kanal bulunamadı. Token geçersiz olabilir.")
            return

        for channel in channels:
            name = channel.get('Name').replace(" ", "_").replace("/", "-").replace("&", "ve")
            stream_data = channel.get('StreamData', {})
            hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
            
            # Kategori kontrolü (Bilgilendirme kanallarını atla)
            cats = channel.get('Categories', [])
            if not hls_url or (cats and cats[0].get('Name') == "Bilgilendirme"):
                continue

            print(f"🎬 {name} için en yüksek kalite ayıklanıyor...")
            
            # İç içe geçmiş m3u8'den en yüksek kaliteyi çek
            final_high_quality_url = get_best_quality_url(hls_url)

            # GitHub için dosyayı oluştur
            file_path = os.path.join(output_dir, f"{name}.m3u8")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write("#EXT-X-VERSION:3\n")
                f.write(f"{final_high_quality_url}\n")

        print(f"\n✅ İşlem tamam! {output_dir} klasöründeki dosyalar artık doğrudan en yüksek kaliteli yayına bakıyor.")
        
    except Exception as e:
        print(f"❌ Ana hata: {e}")

if __name__ == "__main__":
    create_separate_m3u8()
