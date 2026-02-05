import requests
import json
import re
import os
from cloudscraper import CloudScraper

class RecTVPro:
    def __init__(self):
        self.session = CloudScraper()
        self.save_folder = "rectv"
        self.m3u_file = "r2.m3u"

    def slugify(self, name):
        """Kanal ismini dosya sistemine uygun (temiz) hale getirir."""
        rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
        for k,v in rep.items():
            name = name.replace(k, v)
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
        return name

    def get_dynamic_domain(self):
        """Firebase Remote Config üzerinden güncel RecTV domainini sorgular."""
        try:
            print("📡 Firebase üzerinden güncel domain alınıyor...")
            payload = {
                "platformVersion": "25",
                "appInstanceId": "fSrUnUPXQOCIN37mjVhnJo",
                "packageName": "com.rectv.shot",
                "appVersion": "19.3",
                "appId": "1:791583031279:android:244c3d507ab299fcabc01a"
            }
            response = self.session.post(
                url="https://firebaseremoteconfig.googleapis.com/v1/projects/791583031279/namespaces/firebase:fetch",
                headers={
                    "X-Goog-Api-Key": "AIzaSyBbhpzG8Ecohu9yArfCO5tF13BQLhjLahc",
                    "X-Android-Package": "com.rectv.shot",
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)"
                },
                json=payload,
                timeout=15
            )
            data = response.json()
            domains_str = data.get("entries", {}).get("ab_rotating_live_tv_domains", "[]")
            domains_list = json.loads(domains_str)
            
            # Domaini temizle
            main_url = domains_list[0].rstrip('/') if domains_list else "https://cloudlyticsapp.lol"
            print(f"🟢 Başarılı: {main_url}")
            return main_url
        except Exception as e:
            print(f"🔴 Domain çekilemedi, varsayılan kullanılıyor: {e}")
            return "https://cloudlyticsapp.lol"

    def process_channels(self):
        """Domaini günceller ve dosyaları klasöre ayırır."""
        new_domain = self.get_dynamic_domain()
        
        # Klasör yoksa oluştur
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
            print(f"📁 '{self.save_folder}' klasörü oluşturuldu.")

        # r2.m3u dosyasının varlığını kontrol et
        if not os.path.exists(self.m3u_file):
            print(f"⚠️ {self.m3u_file} bulunamadı! İşlem iptal edildi.")
            return

        try:
            with open(self.m3u_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            final_m3u = ["#EXTM3U"]
            current_info = ""
            count = 0

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#EXTM3U"): continue
                
                if line.startswith("#EXTINF"):
                    current_info = line
                elif line.startswith("http"):
                    # Linkteki eski domaini yenisiyle değiştir (Regex)
                    updated_url = re.sub(r'https?://[^/]+', new_domain, line)
                    
                    # Kanal ismini EXTINF satırından çek
                    name_match = re.search(r',(.+)$', current_info)
                    raw_name = name_match.group(1).strip() if name_match else "adsiz-kanal"
                    
                    # Klasöre .m3u8 olarak kaydet
                    safe_name = self.slugify(raw_name)
                    with open(os.path.join(self.save_folder, f"{safe_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write(f"#EXTM3U\n{current_info}\n{updated_url}")
                    
                    # Ana liste için sakla
                    final_m3u.append(f"{current_info}\n{updated_url}")
                    count += 1

            # r2.m3u dosyasını güncelle
            with open(self.m3u_file, 'w', encoding='utf-8') as file:
                file.write("\n".join(final_m3u))

            print(f"🏁 Tamamlandı: {count} kanal güncellendi ve parçalandı.")

        except Exception as e:
            print(f"❌ İşlem sırasında hata: {e}")

if __name__ == "__main__":
    RecTVPro().process_channels()
