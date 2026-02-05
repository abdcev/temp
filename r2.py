import requests
import json
import re
import os
from cloudscraper import CloudScraper

class RecTVScraper:
    def __init__(self):
        self.session = CloudScraper()
        self.save_folder = "rectv"
        self.m3u_file = "r2.m3u"

    def slugify(self, name):
        """Kanal ismini dosya sistemine uygun hale getirir."""
        rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
        for k,v in rep.items():
            name = name.replace(k, v)
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
        return name

    def get_rectv_domain(self):
        """Firebase üzerinden güncel RecTV domainini çeker."""
        try:
            print("🔍 Firebase Remote Config üzerinden domain çekiliyor...")
            response = self.session.post(
                url="https://firebaseremoteconfig.googleapis.com/v1/projects/791583031279/namespaces/firebase:fetch",
                headers={
                    "X-Goog-Api-Key": "AIzaSyBbhpzG8Ecohu9yArfCO5tF13BQLhjLahc",
                    "X-Android-Package": "com.rectv.shot",
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)",
                },
                json={
                    "platformVersion": "25",
                    "appInstanceId": "fSrUnUPXQOCIN37mjVhnJo",
                    "packageName": "com.rectv.shot",
                    "appVersion": "19.3",
                    "countryCode": "TR",
                    "sdkVersion": "22.0.1",
                    "appBuild": "104",
                    "firstOpenTime": "2025-12-21T20:00:00.000Z",
                    "appId": "1:791583031279:android:244c3d507ab299fcabc01a",
                    "languageCode": "tr-TR"
                },
                timeout=15
            )
            data = response.json()
            domains_str = data.get("entries", {}).get("ab_rotating_live_tv_domains", "[]")
            domains_list = json.loads(domains_str)
            
            # Domaini temizle (sondaki slash'ı kaldır)
            main_url = domains_list[0].rstrip('/') if domains_list else "https://cloudlyticsapp.lol"
            print(f"✅ Güncel RecTV domain alındı: {main_url}")
            return main_url
        except Exception as e:
            print(f"🔴 Domain alınamadı: {e}")
            return None

    def process_and_split(self, new_domain):
        """M3U dosyasını günceller ve kanalları klasöre ayırır."""
        if not os.path.exists(self.m3u_file):
            print(f"⚠️ {self.m3u_file} bulunamadı, işlem yapılamıyor.")
            return

        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

        try:
            with open(self.m3u_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            new_m3u_content = []
            current_info = None
            ok_count = 0

            for line in lines:
                line = line.strip()
                if not line: continue
                
                if line.startswith("#EXTINF"):
                    current_info = line
                elif line.startswith("http"):
                    # Domain güncelleme (Regex ile)
                    updated_url = re.sub(r'https?://[^/]+', new_domain, line)
                    
                    # Kanal ismini EXTINF içinden çek
                    name_match = re.search(r',(.+)$', current_info)
                    channel_name = name_match.group(1).strip() if name_match else "adsiz-kanal"
                    
                    # Tekil dosya oluştur
                    safe_name = self.slugify(channel_name)
                    with open(os.path.join(self.save_folder, f"{safe_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write(f"#EXTM3U\n{current_info}\n{updated_url}")
                    
                    # Ana M3U listesi için sakla
                    new_m3u_content.append(f"{current_info}\n{updated_url}")
                    ok_count += 1
                elif line.startswith("#EXTM3U"):
                    new_m3u_content.append(line)

            # Ana m3u dosyasını güncelle
            with open(self.m3u_file, 'w', encoding='utf-8') as file:
                file.write("\n".join(new_m3u_content))

            print(f"🏁 Başarılı: {ok_count} kanal '{self.save_folder}' klasörüne ayrıştırıldı ve {self.m3u_file} güncellendi.")

        except Exception as e:
            print(f"❌ Ayrıştırma hatası: {e}")

    def run(self):
        domain = self.get_rectv_domain()
        if domain:
            self.process_and_split(domain)

if __name__ == "__main__":
    RecTVScraper().run()
