import requests
import re
import urllib3
import json
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoHybridScraper:
    def __init__(self):
        self.api_url = "https://justintvcanli.online/domain.php"
        self.save_folder = "jest"  # Kanal dosyalarının kaydedileceği klasör
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.kanallar = {
            "zirve": "beIN Sports 1 A", "trgoals": "beIN Sports 1 B", "yayin1": "beIN Sports 1 C",
            "b2": "beIN Sports 2", "b3": "beIN Sports 3", "b4": "beIN Sports 4", "b5": "beIN Sports 5",
            "bm1": "beIN Sports 1 Max", "bm2": "beIN Sports 2 Max", "ss1": "S Sports 1",
            "ss2": "S Sports 2", "smarts": "Smart Sports", "sms2": "Smart Sports 2",
            "t1": "Tivibu Sports 1", "t2": "Tivibu Sports 2", "t3": "Tivibu Sports 3",
            "t4": "Tivibu Sports 4", "as": "A Spor", "trtspor": "TRT Spor",
            "trtspor2": "TRT Spor Yıldız", "trt1": "TRT 1", "atv": "ATV",
            "tv85": "TV8.5", "nbatv": "NBA TV", "eu1": "Euro Sport 1", "eu2": "Euro Sport 2",
            "ex1": "Tabii 1", "ex2": "Tabii 2", "ex3": "Tabii 3", "ex4": "Tabii 4",
            "ex5": "Tabii 5", "ex6": "Tabii 6", "ex7": "Tabii 7", "ex8": "Tabii 8"
        }

    def slugify(self, name):
        """Kanal ismini dosya sistemine uygun hale getirir."""
        rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
        for k,v in rep.items():
            name = name.replace(k, v)
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
        return name

    def fetch_assets(self):
        """Aktif domaini tarayarak bulur ve sunucuyu API'den çeker."""
        active_referer = None
        
        print("🌐 Aktif domain (Referer) taranıyor...")
        for i in range(530, 585):
            target = f"https://monotv{i}.com"
            try:
                r = requests.get(target, headers=self.headers, timeout=4, verify=False)
                if r.status_code == 200:
                    active_referer = target + "/"
                    print(f"✅ Aktif Referer Bulundu: {active_referer}")
                    break
            except:
                continue

        print("📡 Yayın sunucusu API'den çekiliyor...")
        stream_server = None
        try:
            rapi = requests.get(self.api_url, headers=self.headers, timeout=10, verify=False)
            if rapi.status_code == 200:
                data = rapi.json()
                stream_server = data.get("baseurl", "").replace("\\", "")
        except:
            pass

        return active_referer, stream_server

    def run(self):
        # 1. Klasör Hazırlığı
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
            print(f"📂 '{self.save_folder}' klasörü oluşturuldu.")

        referer, stream = self.fetch_assets()

        if not referer:
            referer = "https://justintvcanli.online/"
            print("⚠️ Aktif monotv bulunamadı, yedek referer kullanılıyor.")
        
        if not stream:
            print("❌ Sunucu adresi API'den alınamadı.")
            return

        print(f"✅ Final Sunucu: {stream}")
        print(f"✅ Final Referer: {referer}")

        ok_count = 0
        for cid, name in self.kanallar.items():
            safe_name = self.slugify(name)
            file_path = os.path.join(self.save_folder, f"{safe_name}.m3u8")
            
            # Münferit dosya içeriği
            content = [
                "#EXTM3U",
                f'#EXTINF:-1 group-title="JEST SPOR",{name}',
                f'#EXTVLCOPT:http-referrer={referer}',
                f'{stream}{cid}/mono.m3u8'
            ]
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
                ok_count += 1
            except Exception as e:
                print(f"❌ {name} dosyası oluşturulamadı: {e}")
        
        print(f"🏁 Başarılı: {ok_count} kanal '{self.save_folder}' klasörüne kaydedildi.")

if __name__ == "__main__":
    MonoHybridScraper().run()
