import requests
import re
import sys
import os
from datetime import datetime

class AndroTVScraper:
    def __init__(self):
        self.save_folder = "atom"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.channels = [
            ("beIN Sport 1 HD","androstreamlivebiraz1"),
            ("beIN Sport 2 HD","androstreamlivebs2"),
            ("beIN Sport 3 HD","androstreamlivebs3"),
            ("beIN Sport 4 HD","androstreamlivebs4"),
            ("beIN Sport 5 HD","androstreamlivebs5"),
            ("beIN Sport Max 1 HD","androstreamlivebsm1"),
            ("beIN Sport Max 2 HD","androstreamlivebsm2"),
            ("S Sport 1 HD","androstreamlivess1"),
            ("S Sport 2 HD","androstreamlivess2"),
            ("Tivibu Sport HD","androstreamlivets"),
            ("Tivibu Sport 1 HD","androstreamlivets1"),
            ("Tivibu Sport 2 HD","androstreamlivets2"),
            ("Tivibu Sport 3 HD","androstreamlivets3"),
            ("Tivibu Sport 4 HD","androstreamlivets4"),
            ("Smart Sport 1 HD","androstreamlivesm1"),
            ("Smart Sport 2 HD","androstreamlivesm2"),
            ("Euro Sport 1 HD","androstreamlivees1"),
            ("Euro Sport 2 HD","androstreamlivees2"),
            ("Tabii HD","androstreamlivetb"),
            ("Tabii 1 HD","androstreamlivetb1"),
            ("Tabii 2 HD","androstreamlivetb2"),
            ("Tabii 3 HD","androstreamlivetb3"),
            ("Tabii 4 HD","androstreamlivetb4"),
            ("Tabii 5 HD","androstreamlivetb5"),
            ("Tabii 6 HD","androstreamlivetb6"),
            ("Tabii 7 HD","androstreamlivetb7"),
            ("Tabii 8 HD","androstreamlivetb8"),
            ("Exxen HD","androstreamliveexn"),
            ("Exxen 1 HD","androstreamliveexn1"),
            ("Exxen 2 HD","androstreamliveexn2"),
            ("Exxen 3 HD","androstreamliveexn3"),
            ("Exxen 4 HD","androstreamliveexn4"),
            ("Exxen 5 HD","androstreamliveexn5"),
            ("Exxen 6 HD","androstreamliveexn6"),
            ("Exxen 7 HD","androstreamliveexn7"),
            ("Exxen 8 HD","androstreamliveexn8"),
        ]

    def slugify(self, name):
        """Dosya adı için kanal ismini temizler."""
        rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
        for k,v in rep.items():
            name = name.replace(k, v)
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
        return name

    def get_active_assets(self):
        """Aktif domain ve yayın base URL'ini bulur."""
        active_domain = None
        base_url = None

        print("🔍 Aktif domain aranıyor (birazcikspor)...")
        for i in range(25, 150): # Menzil ihtiyaca göre artırılabilir
            url = f"https://birazcikspor{i}.xyz/"
            try:
                r = requests.head(url, timeout=3, headers=self.headers)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Domain bulundu: {active_domain}")
                    break
            except: continue

        if active_domain:
            try:
                html = requests.get(active_domain, timeout=5, headers=self.headers).text
                m = re.search(r'id="matchPlayer"[^>]+src="event\.html\?id=([^"]+)"', html)
                if m:
                    event_id = m.group(1)
                    event_url = f"{active_domain}event.html?id={event_id}"
                    e_html = requests.get(event_url, timeout=5, headers=self.headers).text
                    b = re.search(r'const\s+baseurls\s*=\s*\[\s*"([^"]+)"', e_html)
                    if b:
                        base_url = b.group(1)
                        print(f"✅ Base URL bulundu: {base_url}")
            except Exception as e:
                print(f"⚠️ Veri çekilirken hata: {e}")

        return active_domain, base_url

    def run(self):
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

        domain, base_url = self.get_active_assets()

        # Klasör içi dosyalar ve ana M3U için listeler
        m3u_lines = ["#EXTM3U"]
        ok_count = 0

        # Eğer her şey yolundaysa işle
        if domain and base_url:
            for name, cid in self.channels:
                full_url = f"{base_url}{cid}.m3u8"
                safe_name = self.slugify(name)
                
                # Tekil dosya içeriği
                file_content = [
                    "#EXTM3U",
                    f'#EXTINF:-1 tvg-id="sport.tr" group-title="Atom TV",{name}',
                    full_url
                ]
                
                # Dosyayı kaydet
                with open(os.path.join(self.save_folder, f"{safe_name}.m3u8"), "w", encoding="utf-8") as f:
                    f.write("\n".join(file_content))
                
                # Ana liste için ekle
                m3u_lines.append(f'#EXTINF:-1 tvg-id="sport.tr" group-title="Atom TV",{name}')
                m3u_lines.append(full_url)
                ok_count += 1

        # Geriye dönük uyumluluk için an.m3u dosyasını da oluştur/güncelle
        with open("an.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))

        print(f"🏁 İşlem Tamamlandı: {ok_count} kanal '{self.save_folder}' klasörüne kaydedildi.")

if __name__ == "__main__":
    AndroTVScraper().run()
