import re
import os
import shutil
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

# Ayarlar
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
OUTPUT_FOLDER = "selcuk"

def find_active_domain(start=1825, end=1900):
    """Aktif yayın domainini tarayarak bulur."""
    print(f"🔍 {start}-{end} aralığında aktif domain aranıyor...")
    for i in range(start, end + 1):
        url = f"https://www.selcuksportshd{i}.xyz/"
        try:
            req = Request(url, headers=HEADERS)
            # Timeout süresini 3 saniyeye düşürerek taramayı hızlandırıyoruz
            with urlopen(req, timeout=3) as response:
                html = response.read().decode('utf-8')
                if "uxsyplayer" in html or "m3u8" in html:
                    print(f"✅ Aktif domain bulundu: {url}")
                    return url, html
        except:
            continue
    return None, None

def slugify(name):
    """Dosya isimlerini Türkçe karakterlerden arındırır ve düzenler."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k, v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

def get_player_links(html):
    """Ana sayfadaki kanal linklerini ve isimlerini toplar."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    # Sitedeki data-url özniteliğine sahip a etiketlerini bulur
    for a in soup.find_all("a", attrs={"data-url": True}):
        data_url = a["data-url"].strip()
        if data_url.startswith("/"):
            data_url = "https://" + data_url.lstrip("/")
        
        name = a.text.strip()
        if not name:
            name = data_url.split("id=")[-1] if "id=" in data_url else "Kanal"
        
        links.append({"url": data_url, "name": name})
    return links

def get_m3u8_url(player_url, referer):
    """Player sayfasından asıl m3u8 yayın linkini ayıklar."""
    try:
        req = Request(player_url, headers={"User-Agent": HEADERS["User-Agent"], "Referer": referer})
        with urlopen(req, timeout=7) as response:
            html = response.read().decode('utf-8')
        
        patterns = [
            r'this\.baseStreamUrl\s*=\s*"([^"]+)"',
            r"this\.baseStreamUrl\s*=\s*'([^']+)'",
            r'baseStreamUrl\s*:\s*"([^"]+)"',
            r"baseStreamUrl\s*:\s*'([^']+)'"
        ]
        
        base_url = None
        for p in patterns:
            m = re.search(p, html)
            if m:
                base_url = m.group(1)
                break
        
        if not base_url: return None
        
        m_id = re.search(r"id=([a-zA-Z0-9]+)", player_url)
        if not m_id: return None
        
        stream_id = m_id.group(1)
        if not base_url.endswith("/"): base_url += "/"
        
        return f"{base_url}{stream_id}/playlist.m3u8"
    except:
        return None

def create_individual_files():
    """Ana akış fonksiyonu: Klasörü temizler ve m3u8 dosyalarını oluşturur."""
    domain, html = find_active_domain()
    if not html:
        print("❌ Çalışan domain bulunamadı! Lütfen aralığı kontrol edin.")
        return

    # KLASÖR TEMİZLİĞİ: Her zaman en güncel listeyi tutmak için
    if os.path.exists(OUTPUT_FOLDER):
        print(f"🧹 '{OUTPUT_FOLDER}' klasörü temizleniyor...")
        shutil.rmtree(OUTPUT_FOLDER)
    
    os.makedirs(OUTPUT_FOLDER)
    print(f"📂 '{OUTPUT_FOLDER}' klasörü oluşturuldu.")

    players = get_player_links(html)
    if not players:
        print("⚠️ Hiç kanal linki bulunamadı.")
        return

    print(f"📺 {len(players)} kanal işleniyor...\n")
    success_count = 0

    for ch in players:
        m3u8_link = get_m3u8_url(ch["url"], domain)
        if m3u8_link:
            file_name = f"{slugify(ch['name'])}.m3u8"
            file_path = os.path.join(OUTPUT_FOLDER, file_name)
            
            # M3U8 Dosya İçeriği
            content = [
                "#EXTM3U",
                f"#EXTINF:-1,{ch['name']}",
                f"#EXTVLCOPT:http-referrer={domain}",
                f"#EXTVLCOPT:http-user-agent={HEADERS['User-Agent']}",
                m3u8_link
            ]
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
                print(f"✅ Oluşturuldu: {file_name}")
                success_count += 1
            except Exception as e:
                print(f"⚠️ Yazma hatası ({ch['name']}): {e}")
        else:
            print(f"❌ Link çekilemedi: {ch['name']}")

    print(f"\n🚀 İşlem Tamamlandı!")
    print(f"📊 Toplam: {len(players)} | Başarılı: {success_count} | Başarısız: {len(players)-success_count}")

if __name__ == "__main__":
    create_individual_files()
