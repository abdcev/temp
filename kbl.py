import requests
import json
import gzip
import os
import re
from io import BytesIO

def get_best_quality_url(master_url):
    """Master m3u8 linkinden en yüksek çözünürlüğü seçer"""
    try:
        r = requests.get(master_url, timeout=10)
        lines = r.text.splitlines()
        
        best_bandwidth = -1
        best_url = master_url # Bulamazsa orijinali döner
        
        for i in range(len(lines)):
            if "#EXT-X-STREAM-INF" in lines[i]:
                # BANDWIDTH değerini yakala
                bandwidth_match = re.search(r"BANDWIDTH=(\d+)", lines[i])
                if bandwidth_match:
                    bandwidth = int(bandwidth_match.group(1))
                    if bandwidth > best_bandwidth:
                        best_bandwidth = bandwidth
                        # Bir sonraki satır linktir
                        sub_url = lines[i+1]
                        if not sub_url.startswith("http"):
                            # Göreceli link ise ana URL ile birleştir
                            base_url = master_url.rsplit('/', 1)[0]
                            best_url = f"{base_url}/{sub_url}"
                        else:
                            best_url = sub_url
        return best_url
    except:
        return master_url

def create_separate_m3u8():
    url = "https://core-api.kablowebtv.com/api/channels"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9..." # Buraya güncel token gelmeli
    }

    # Kanalların kaydedileceği klasör
    output_dir = "kanallar"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        response = requests.get(url, headers=headers, params={"checkip": "false"}, timeout=30)
        
        # Gzip kontrolü
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)
        channels = data.get('Data', {}).get('AllChannels', [])

        for channel in channels:
            name = channel.get('Name').replace(" ", "_").replace("/", "-") # Dosya adı uyumlu yap
            stream_data = channel.get('StreamData', {})
            hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
            
            if not hls_url or channel.get('Categories', [{}])[0].get('Name') == "Bilgilendirme":
                continue

            print(f"🔄 İşleniyor: {name}")
            
            # En yüksek kaliteyi bul
            final_url = get_best_quality_url(hls_url)

            # Ayrı m3u8 dosyası oluştur
            file_path = os.path.join(output_dir, f"{name}.m3u8")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"#EXT-X-VERSION:3\n")
                f.write(f"{final_url}\n")

        print("\n✅ Tüm kanallar için ayrı m3u8 dosyaları 'kanallar' klasöründe oluşturuldu.")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    create_separate_m3u8()
