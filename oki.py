import os
import re
from datetime import datetime

# ---------------- NexaTVManager ----------------
class NexaTVManager:
    def __init__(self):
        self.proxy_prefix = "https://api.codetabs.com/v1/proxy/?quest="
        self.base_stream_url = "https://andro.okan11gote12sokan.cfd/checklist/"
        self.logo_url = "https://i.hizliresim.com/8xzjgqv.jpg"
        self.group_title = "NexaTV"
        self.save_folder = "nexa"  # Kanal dosyalarının toplanacağı klasör
        self.channels = [
            {"name": "TR:beIN Sport 1 HD", "path": "androstreamlivebs1.m3u8"},
            {"name": "TR:beIN Sport 2 HD", "path": "androstreamlivebs2.m3u8"},
            {"name": "TR:beIN Sport 3 HD", "path": "androstreamlivebs3.m3u8"},
            {"name": "TR:beIN Sport 4 HD", "path": "androstreamlivebs4.m3u8"},
            {"name": "TR:beIN Sport 5 HD", "path": "androstreamlivebs5.m3u8"},
            {"name": "TR:beIN Sport Max 1 HD", "path": "androstreamlivebsm1.m3u8"},
            {"name": "TR:beIN Sport Max 2 HD", "path": "androstreamlivebsm2.m3u8"},
            {"name": "TR:S Sport 1 HD", "path": "androstreamlivess1.m3u8"},
            {"name": "TR:S Sport 2 HD", "path": "androstreamlivess2.m3u8"},
            {"name": "TR:Tivibu Sport HD", "path": "androstreamlivets.m3u8"},
            {"name": "TR:Tivibu Sport 1 HD", "path": "androstreamlivets1.m3u8"},
            {"name": "TR:Tivibu Sport 2 HD", "path": "androstreamlivets2.m3u8"},
            {"name": "TR:Tivibu Sport 3 HD", "path": "androstreamlivets3.m3u8"},
            {"name": "TR:Tivibu Sport 4 HD", "path": "androstreamlivets4.m3u8"},
            {"name": "TR:Smart Sport 1 HD", "path": "androstreamlivesm1.m3u8"},
            {"name": "TR:Smart Sport 2 HD", "path": "androstreamlivesm2.m3u8"},
            {"name": "TR:Euro Sport 1 HD", "path": "androstreamlivees1.m3u8"},
            {"name": "TR:Euro Sport 2 HD", "path": "androstreamlivees2.m3u8"},
            {"name": "TR:Tabii HD", "path": "androstreamlivetb.m3u8"},
            {"name": "TR:Tabii 1 HD", "path": "androstreamlivetb1.m3u8"},
            {"name": "TR:Tabii 2 HD", "path": "androstreamlivetb2.m3u8"},
            {"name": "TR:Tabii 3 HD", "path": "androstreamlivetb3.m3u8"},
            {"name": "TR:Tabii 4 HD", "path": "androstreamlivetb4.m3u8"},
            {"name": "TR:Tabii 5 HD", "path": "androstreamlivetb5.m3u8"},
            {"name": "TR:Tabii 6 HD", "path": "androstreamlivetb6.m3u8"},
            {"name": "TR:Tabii 7 HD", "path": "androstreamlivetb7.m3u8"},
            {"name": "TR:Tabii 8 HD", "path": "androstreamlivetb8.m3u8"},
            {"name": "TR:Exxen HD", "path": "androstreamliveexn.m3u8"},
            {"name": "TR:Exxen 1 HD", "path": "androstreamliveexn1.m3u8"},
            {"name": "TR:Exxen 2 HD", "path": "androstreamliveexn2.m3u8"},
            {"name": "TR:Exxen 3 HD", "path": "androstreamliveexn3.m3u8"},
            {"name": "TR:Exxen 4 HD", "path": "androstreamliveexn4.m3u8"},
            {"name": "TR:Exxen 5 HD", "path": "androstreamliveexn5.m3u8"},
            {"name": "TR:Exxen 6 HD", "path": "androstreamliveexn6.m3u8"},
            {"name": "TR:Exxen 7 HD", "path": "androstreamliveexn7.m3u8"},
        ]

    def slugify(self, name):
        """Kanal adını dosya sistemine uygun temiz bir hale getirir."""
        name = name.replace("TR:", "") # Başındaki TR: kısmını temizle
        rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
        for k,v in rep.items():
            name = name.replace(k, v)
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
        return name

    def dosyalari_olustur(self):
        """Her kanal için ayrı m3u8 dosyası oluşturur."""
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
            print(f"📂 '{self.save_folder}' klasörü oluşturuldu.")

        ok_count = 0
        for channel in self.channels:
            # URL Hazırlama
            real_url = f"{self.base_stream_url}{channel['path']}"
            stream_url = f"{self.proxy_prefix}{real_url}"
            
            # Dosya Adı Hazırlama
            safe_name = self.slugify(channel['name'])
            file_name = f"{safe_name}.m3u8"
            file_path = os.path.join(self.save_folder, file_name)

            # Dosya İçeriği
            content = [
                "#EXTM3U",
                f'#EXTINF:-1 tvg-id="sport.tr" tvg-logo="{self.logo_url}" group-title="{self.group_title}",{channel["name"]}',
                stream_url,
                f"\n# Generated: {datetime.utcnow().isoformat()}"
            ]

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
                ok_count += 1
            except Exception as e:
                print(f"❌ {channel['name']} yazılamadı: {e}")

        print(f"✅ İşlem Tamamlandı: {ok_count} kanal dosyası '{self.save_folder}' klasörüne kaydedildi.")


# ---------------- Ana Çalıştırma ----------------
if __name__ == "__main__":
    print(f"--- NexaTV Görevi Başlatıldı ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    manager = NexaTVManager()
    manager.dosyalari_olustur()
    print("--- Görev Tamamlandı ---")
