import requests
import re
import os
import shutil

# AtomSporTV Ayarları
START_URL = "https://url24.link/AtomSporTV"
SAVE_FOLDER = "rnl"# Kanalların kaydedileceği klasör

GREEN = "\033[92m"
RESET = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://url24.link/'
}

def slugify(name):
    """Kanal isimlerini dosya ve URL uyumlu hale getirir."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

def get_base_domain():
    """Ana domain'i bul"""
    try:
        response = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in response.headers:
            location1 = response.headers['location']
            response2 = requests.get(location1, headers=headers, allow_redirects=False, timeout=10)
            if 'location' in response2.headers:
                base_domain = response2.headers['location'].strip().rstrip('/')
                print(f"Ana Domain: {base_domain}")
                return base_domain
        return "https://www.atomsportv480.top"
    except Exception as e:
        print(f"Domain hatası: {e}")
        return "https://www.atomsportv480.top"

def get_channel_m3u8(channel_id, base_domain):
    """PHP mantığı ile m3u8 linkini al"""
    try:
        matches_url = f"{base_domain}/matches?id={channel_id}"
        response = requests.get(matches_url, headers=headers, timeout=10)
        html = response.text
        
        fetch_match = re.search(r'fetch\("(.*?)"', html) or re.search(r'fetch\(\s*["\'](.*?)["\']', html)
        
        if fetch_match:
            fetch_url = fetch_match.group(1).strip()
            custom_headers = headers.copy()
            custom_headers['Origin'] = base_domain
            custom_headers['Referer'] = base_domain
            
            if not fetch_url.endswith(channel_id):
                fetch_url = fetch_url + channel_id
            
            response2 = requests.get(fetch_url, headers=custom_headers, timeout=10)
            fetch_data = response2.text
            
            m3u8_match = re.search(r'"deismackanal":"(.*?)"', fetch_data) or \
                         re.search(r'"(?:stream|url|source)":\s*"(.*?\.m3u8)"', fetch_data)
            
            if m3u8_match:
                return m3u8_match.group(1).replace('\\', '')
        return None
    except:
        return None

def get_tv_channels():
    """Kanal listesini döndür"""
    return [
        ("bein-sports-1", "BEIN SPORTS 1"),
        ("bein-sports-2", "BEIN SPORTS 2"),
        ("bein-sports-3", "BEIN SPORTS 3"),
        ("bein-sports-4", "BEIN SPORTS 4"),
        ("s-sport", "S SPORT"),
        ("s-sport-2", "S SPORT 2"),
        ("tivibu-spor-1", "TİVİBU SPOR 1"),
        ("tivibu-spor-2", "TİVİBU SPOR 2"),
        ("tivibu-spor-3", "TİVİBU SPOR 3"),
        ("trt-spor", "TRT SPOR"),
        ("trt-yildiz", "TRT YILDIZ"),
        ("trt1", "TRT 1"),
        ("aspor", "ASPOR"),
    ]

def main():
    print(f"{GREEN}AtomSporTV Çoklu Dosya Oluşturucu{RESET}")
    print("=" * 60)
    
    # 1. Klasör Hazırlığı
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
        print(f"📂 '{SAVE_FOLDER}' klasörü oluşturuldu.")
    else:
        print(f"📂 '{SAVE_FOLDER}' klasörü zaten var, dosyalar güncelleniyor...")

    # 2. Ana domain'i bul
    base_domain = get_base_domain()
    
    # 3. Kanalları Test Et ve Kaydet
    tv_channels = get_tv_channels()
    ok = 0

    print(f"\n{len(tv_channels)} kanal işleniyor...")

    for i, (channel_id, name) in enumerate(tv_channels):
        print(f"{i+1:2d}. {name}...", end=" ", flush=True)
        
        m3u8_url = get_channel_m3u8(channel_id, base_domain)
        
        if m3u8_url:
            file_name = f"{slugify(name)}.m3u8"
            file_path = os.path.join(SAVE_FOLDER, file_name)
            
            # Tekil M3U8 dosya içeriği
            content = [
                "#EXTM3U",
                f"#EXTINF:-1,{name}",
                f"#EXTVLCOPT:http-referrer={base_domain}",
                f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}",
                m3u8_url
            ]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
                
            print(f"{GREEN}✓ ({file_name}){RESET}")
            ok += 1
        else:
            print("✗ (Link bulunamadı)")

    print("\n" + "=" * 60)
    print(f"🚀 İşlem Tamamlandı! {ok} dosya '{SAVE_FOLDER}' klasörüne kaydedildi.")

if __name__ == "__main__":
    main()
