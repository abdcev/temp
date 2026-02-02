import requests
import json
import gzip
from io import BytesIO
import os

def get_canli_tv_m3u8_best_folder():
    url = "https://core-api.kablowebtv.com/api/channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"  # token'ını buraya koy
    }

    params = {"checkip": "false"}

    try:
        print("📡 CanliTV API'den veri alınıyor...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        # Gzip varsa aç
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')
        
        data = json.loads(content)
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            print("❌ CanliTV API'den geçerli veri alınamadı!")
            return False
        
        channels = data['Data']['AllChannels']
        print(f"✅ {len(channels)} kanal bulundu")

        # Ana klasör ve best alt klasörü
        base_folder = "kbl"
        best_folder = os.path.join(base_folder, "best")
        os.makedirs(best_folder, exist_ok=True)
        print(f"Klasörler oluşturuldu: {base_folder}/ ve {best_folder}/")

        kanal_sayisi = 0

        for idx, channel in enumerate(channels, 1):
            name = channel.get('Name')
            stream_data = channel.get('StreamData', {})
            hls_master_url = stream_data.get('HlsStreamUrl') if stream_data else None
            categories = channel.get('Categories', [])

            if not name or not hls_master_url:
                continue

            group = categories[0].get('Name', 'Genel') if categories else 'Genel'
            if group == "Bilgilendirme":
                continue

            # Kanal adını safe karaktere çevir
            safe_name = "".join(c for c in name if c.isalnum() or c in " _-").rstrip()
            file_path = os.path.join(best_folder, f"{safe_name}.m3u8")

            # Master m3u8'i çek
            try:
                master_resp = requests.get(hls_master_url, headers=headers, timeout=20)
                master_resp.raise_for_status()
                master_lines = master_resp.text.splitlines()
            except:
                print(f"❌ {name} için master m3u8 alınamadı")
                continue

            # En yüksek kaliteyi seç (RESOLUTION en yüksek olan)
            best_url = None
            best_res = 0
            for i, line in enumerate(master_lines):
                if line.startswith("#EXT-X-STREAM-INF"):
                    parts = line.split(",")
                    res_part = [p for p in parts if "RESOLUTION=" in p]
                    if res_part:
                        res_text = res_part[0].split("=")[1]
                        try:
                            width, height = map(int, res_text.split("x"))
                            if height > best_res:
                                best_res = height
                                if i + 1 < len(master_lines):
                                    best_url = master_lines[i+1].strip()
                        except:
                            continue

            if not best_url:
                best_url = hls_master_url  # kalite bulunamazsa master kullan

            # Dosyaya yaz
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"#EXTINF:-1,{name}\n")
                f.write(best_url + "\n")

            kanal_sayisi += 1

        print(f"📺 Best kalite m3u8 klasörü oluşturuldu! ({kanal_sayisi} kanal)")
        return True

    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    get_canli_tv_m3u8_best_folder()
