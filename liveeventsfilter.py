import requests
import sys
import os
import re
from pathlib import Path

TIMEOUT = 10
VALID_CONTENT_TYPES = [
    "application/vnd.apple.mpegurl",
    "application/x-mpegURL",
    "video/mp4",
    "audio/mpeg",
    "video/ts",
    "video/x-flv",
]

def slugify(name):
    """Kanal ismini dosya sistemine uygun hale getirir."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

def is_stream_playable(url: str, headers=None) -> bool:
    headers = headers or {}
    try:
        response = requests.head(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code < 400:
            content_type = response.headers.get("Content-Type", "").split(";")[0]
            if content_type in VALID_CONTENT_TYPES:
                return True
    except requests.RequestException:
        pass

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
        if response.status_code < 400:
            content_type = response.headers.get("Content-Type", "").split(";")[0]
            return content_type in VALID_CONTENT_TYPES
    except requests.RequestException:
        return False
    return False

def process_and_split_m3u(input_path: str, output_folder: str = "filter"):
    # Klasör oluştur
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📂 '{output_folder}' klasörü oluşturuldu.")

    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]

    buffer_tags = []
    buffer_vlcopt = []
    count = 0

    for line in lines:
        if line.startswith("#EXTINF"):
            buffer_tags.append(line)
        elif line.startswith("#EXTVLCOPT"):
            buffer_vlcopt.append(line)
        elif line.strip() and not line.startswith("#"):
            url = line.strip()
            
            # Header'ları hazırla
            headers = {}
            for opt in buffer_vlcopt:
                if opt.startswith("#EXTVLCOPT:"):
                    key_value = opt[len("#EXTVLCOPT:"):].split("=", 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        key = key.lower()
                        if key == "http-referrer": headers["Referer"] = value
                        elif key == "http-origin": headers["Origin"] = value
                        elif key == "http-user-agent": headers["User-Agent"] = value

            print(f"Kontrol ediliyor: {url}")
            if is_stream_playable(url, headers=headers):
                # Kanal adını ayıkla
                name_match = re.search(r',([^,]+)$', buffer_tags[0]) if buffer_tags else None
                raw_name = name_match.group(1).strip() if name_match else f"kanal-{count}"
                
                safe_name = slugify(raw_name)
                file_path = os.path.join(output_folder, f"{safe_name}.m3u8")

                # Münferit dosya içeriği
                content = ["#EXTM3U"]
                content.extend(buffer_tags)
                content.extend(buffer_vlcopt)
                content.append(url)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
                
                print(f"  ✓ Çalışıyor: {safe_name}.m3u8")
                count += 1
            else:
                print("  ✗ Çalışmıyor")

            # Buffer temizle
            buffer_tags = []
            buffer_vlcopt = []

    print(f"\n🚀 Tamamlandı! {count} çalışan kanal '{output_folder}' klasörüne ayrıştırıldı.")

if __name__ == "__main__":
    # Kullanım: python script_adi.py giriş.m3u
    if len(sys.argv) < 2:
        print("Kullanım: python filter_script.py input.m3u")
        sys.exit(1)

    input_m3u = sys.argv[1]

    if not Path(input_m3u).exists():
        print("Giriş dosyası bulunamadı.")
        sys.exit(1)

    process_and_split_m3u(input_m3u)
