import requests
import json
import gzip
import os
import re
from io import BytesIO

# --- DOSYA ADI TEMİZLEME FONKSİYONU ---
def slugify(name):
    """Kanal isimlerini dosya sistemine ve URL yapısına uygun hale getirir."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

# --- YOUTUBE FORMATI OLUŞTURUCU FONKSİYON ---
def get_youtube_style_raw(master_url, auth_headers):
    """Master URL'ye gider, içindeki tüm kaliteleri ayıklar ve tam linkleri dizer."""
    try:
        r = requests.get(master_url, headers=auth_headers, timeout=10)
        if r.status_code != 200:
            return master_url # Hata durumunda direkt linki dön
            
        lines = r.text.splitlines()
        best_link = master_url
        
        base_url = master_url.rsplit('/', 1)[0]
        
        # M3U8 içinde dolaşıp en yüksek kaliteyi veya ilk linki bulalım
        for i in range(len(lines)):
            if not lines[i].startswith("#") and lines[i].strip():
                next_line = lines[i].strip()
                if not next_line.startswith("http"):
                    best_link = f"{base_url}/{next_line}"
                else:
                    best_link = next_line
                break # İlk bulduğumuz stream linkini alıyoruz
                
        return best_link
    except:
        return master_url

# --- ANA KOD ---
def get_canli_tv_m3u():
    url = "https://core-api.kablowebtv.com/api/channels"
    save_folder = "kablo"
    main_m3u_file = "kbl.m3u"
    
    # --- KLASÖR KONTROLÜ ---
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"📂 '{save_folder}' klasörü oluşturuldu.")
    else:
        print(f"📂 '{save_folder}' klasörü mevcut, dosyalar güncelleniyor...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://tvheryerde.com",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmBe-08k7YlnuQqJE"
    }

    try:
        print("📡 API'den kanallar çekiliyor...")
        response = requests.get(url, headers=headers, params={"checkip": "false"}, timeout=30)
        
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')
        
        data = json.loads(content)
        channels = data['Data']['AllChannels']

        ok = 0
        main_m3u_content = ["#EXTM3U"] # Ana dosya içeriği başlangıcı

        for channel in channels:
            name = channel.get('Name')
            hls_url = channel.get('StreamData', {}).get('HlsStreamUrl')
            logo = channel.get('LogoUrl', '')
            
            if not name or not hls_url: continue
            if channel.get('Categories') and channel['Categories'][0].get('Name') == "Bilgilendirme": continue

            # Dosya adını güvenli hale getir
            safe_name = slugify(name)
            file_name = f"{safe_name}.m3u8"
            
            print(f"🎬 {name} işleniyor...")
            
            # Alt m3u8 linkini çöz (En yüksek çözünürlük linkini almak için)
            resolved_url = get_youtube_style_raw(hls_url, headers)
            
            # 1. Tekil dosyayı kaydet (İsteğinize göre tam içeriği de yazabiliriz)
            with open(os.path.join(save_folder, file_name), "w", encoding="utf-8") as f:
                f.write(f"#EXTM3U\n{resolved_url}")
            
            # 2. Ana m3u listesine ekle
            main_m3u_content.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}",{name}')
            main_m3u_content.append(resolved_url)
            
            ok += 1

        # --- kbl.m3u DOSYASINI KAYDET ---
        with open(main_m3u_file, "w", encoding="utf-8") as f:
            f.write("\n".join(main_m3u_content))

        print(f"\n✅ İşlem başarılı!")
        print(f"📁 Tekil kanallar '{save_folder}' klasörüne kaydedildi.")
        print(f"📄 Ana liste '{main_m3u_file}' olarak oluşturuldu.")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    get_canli_tv_m3u()
