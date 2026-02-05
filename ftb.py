import requests
import re
import sys
import os
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/index.html"
SAVE_FOLDER = "ftb"  # Kanalların kaydedileceği klasör
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def slugify(name):
    """Kanal isimlerini dosya adı için temizler."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

def get_active_domain():
    """Yönlendirme sayfasından güncel inattv domainini çeker."""
    try:
        print("🔍 Aktif domain yönlendirme sayfasından alınıyor...")
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        match = re.search(r'URL=(https?://[^">]+)', r.text)
        if match:
            domain = match.group(1).rstrip('/')
            print(f"✅ Aktif domain bulundu: {domain}")
            return domain
    except Exception as e:
        print(f"❌ Domain çekilirken hata: {e}")
    return None

def resolve_base_url(active_domain):
    """Yayın sunucusunun base adresini bulur."""
    target = f"{active_domain}/channel.html?id=yayininat"
    try:
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
        
        alt_match = re.search(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site)/)', r.text)
        if alt_match:
            return alt_match.group(1).rstrip('/') + "/"
    except: pass
    return None

def save_individual_m3u8(name, cid, base_url, active_domain, group):
    """Her kanal için ayrı m3u8 dosyası oluşturur."""
    safe_name = slugify(name)
    file_path = os.path.join(SAVE_FOLDER, f"{safe_name}.m3u8")
    
    content = [
        "#EXTM3U",
        f'#EXTINF:-1 group-title="{group}",{name}',
        f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}',
        f'#EXTVLCOPT:http-referrer={active_domain}/',
        f'{base_url}{cid}/mono.m3u8'
    ]
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        return True
    except:
        return False

def main():
    # Klasör hazırlığı
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
    
    active_domain = get_active_domain()
    if not active_domain:
        sys.exit("❌ Başlangıç domaini bulunamadı.")

    base_url = resolve_base_url(active_domain)
    if not base_url:
        base_url = "https://mm9.d72577a9dd0ec19.sbs/" 
        print(f"⚠️ Sunucu otomatik bulunamadı, fallback kullanılıyor: {base_url}")
    else:
        print(f"✅ Yayın sunucusu tespit edildi: {base_url}")

    fixed_channels = {
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

    try:
        print("📡 Veriler işleniyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        count = 0
        # 1. Canlı Maçlar Bölümü
        matches_tab = soup.find(id="matches-tab")
        if matches_tab:
            for a in matches_tab.find_all("a", href=re.compile(r'id=')):
                cid_match = re.search(r'id=([^&]+)', a["href"])
                name_tag = a.find(class_="channel-name")
                status_tag = a.find(class_="channel-status")
                if cid_match and name_tag:
                    cid = cid_match.group(1)
                    status = status_tag.get_text(strip=True) if status_tag else 'CANLI'
                    title = f"{status} | {name_tag.get_text(strip=True)}"
                    if save_individual_m3u8(title, cid, base_url, active_domain, "Canlı Maçlar"):
                        count += 1

        # 2. Sabit Kanallar Bölümü
        for cid, name in fixed_channels.items():
            if save_individual_m3u8(name, cid, base_url, active_domain, "7/24 Kanallar"):
                count += 1

        print(f"🏁 BAŞARILI → {count} adet kanal dosyası '{SAVE_FOLDER}' klasörüne oluşturuldu.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
