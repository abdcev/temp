#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import requests
import os
import sys
from typing import Dict, List, Optional
from urllib.parse import urljoin

# ==================== YAPILANDIRMA ====================
DEFAULT_MAIN_URL = 'https://m.prectv60.lol'
DEFAULT_SW_KEY = '4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452/'
DEFAULT_USER_AGENT = 'okhttp/4.12.0/'
DEFAULT_REFERER = 'https://twitter.com/'
PAGE_COUNT = 4
M3U_USER_AGENT = 'googleusercontent'
SAVE_FOLDER = "rectv"

# GitHub kaynak dosyası (Kotlin dosyası)
SOURCE_URL_RAW = 'https://raw.githubusercontent.com/nikyokki/nik-cloudstream/refs/heads/master/RecTV/src/main/kotlin/com/keyiflerolsun/RecTV.kt'

# ==================== YARDIMCI FONKSİYONLAR ====================

def slugify(name: str) -> str:
    """Kanal ismini dosya sistemine uygun, temiz bir hale getirir."""
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k, v in rep.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

def fetch_github_content():
    """GitHub'dan güncel parametreleri içeren Kotlin dosyasını çeker."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SOURCE_URL_RAW, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"⚠️ GitHub içeriği alınamadı: {e}")
    return None

def parse_github_headers(github_content):
    """Kotlin kodundan mainUrl, swKey ve userAgent bilgilerini ayıklar."""
    headers = {'mainUrl': None, 'swKey': None, 'userAgent': None, 'referer': None}
    if not github_content: return headers
    
    # Regex ile ayıklama
    m_url = re.search(r'override\s+var\s+mainUrl\s*=\s*"([^"]+)"', github_content)
    s_key = re.search(r'private\s+(val|var)\s+swKey\s*=\s*"([^"]+)"', github_content)
    u_agent = re.search(r'headers\s*=\s*mapOf\([^)]*"user-agent"[^)]*to[^"]*"([^"]+)"', github_content, re.DOTALL)
    ref = re.search(r'referer\s*=\s*"([^"]+)"', github_content)

    if m_url: headers['mainUrl'] = m_url.group(1)
    if s_key: headers['swKey'] = s_key.group(2)
    if u_agent: headers['userAgent'] = u_agent.group(1)
    if ref: headers['referer'] = ref.group(1)
    
    return headers

def test_api(main_url, sw_key, user_agent, referer):
    """Bulunan parametrelerin çalışıp çalışmadığını test eder."""
    test_url = f"{main_url}/api/channel/by/filtres/0/0/0/{sw_key}"
    headers = {'User-Agent': user_agent, 'Referer': referer}
    try:
        r = requests.get(test_url, headers=headers, timeout=10, verify=False)
        return r.status_code == 200 and isinstance(r.json(), list)
    except:
        return False

# ==================== ANA İŞLEM ====================

def main():
    # 1. Klasörü hazırla
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    # 2. Parametreleri al (GitHub -> Varsayılan)
    content = fetch_github_content()
    headers_data = parse_github_headers(content)
    
    main_url = headers_data['mainUrl'] or DEFAULT_MAIN_URL
    sw_key = headers_data['swKey'] or DEFAULT_SW_KEY
    user_agent = headers_data['userAgent'] or DEFAULT_USER_AGENT
    referer = headers_data['referer'] or DEFAULT_REFERER

    print(f"📡 Kullanılan Domain: {main_url}")

    # 3. Kanalları Çek ve Kaydet
    m3u_lines = ["#EXTM3U"]
    total_channels = 0
    api_headers = {'User-Agent': user_agent, 'Referer': referer}

    for page in range(PAGE_COUNT):
        api_url = f"{main_url}/api/channel/by/filtres/0/0/{page}/{sw_key}"
        try:
            response = requests.get(api_url, headers=api_headers, timeout=20, verify=False)
            if response.status_code != 200: continue
            
            data = response.json()
            for item in data:
                if 'sources' in item and item['sources']:
                    for src in item['sources']:
                        if src.get('type') == 'm3u8':
                            title = item.get('title', 'Kanal')
                            
                            # Filtre: Sadece Spor kategorisi (Orijinal mantığın)
                            # if categories != "Spor" ... (gerekirse ekle)
                            
                            img = item.get('image', '')
                            if img and not img.startswith('http'):
                                img = urljoin(main_url + '/', img.lstrip('/'))

                            # Kanal Bilgileri
                            inf = f'#EXTINF:-1 tvg-id="{item.get("id")}" tvg-logo="{img}" group-title="Rec TV",{title}'
                            opts = f'#EXTVLCOPT:http-user-agent={M3U_USER_AGENT}\n#EXTVLCOPT:http-referrer={referer}'
                            stream_url = src['url']

                            # Klasöre kaydet
                            safe_name = slugify(title)
                            with open(os.path.join(SAVE_FOLDER, f"{safe_name}.m3u8"), "w", encoding="utf-8") as f:
                                f.write(f"#EXTM3U\n{inf}\n{opts}\n{stream_url}")

                            # Ana listeye ekle
                            m3u_lines.append(f"{inf}\n{opts}\n{stream_url}")
                            total_channels += 1
            print(f"✅ Sayfa {page} işlendi.")
        except Exception as e:
            print(f"⚠️ Sayfa {page} hatası: {e}")

    # 4. r.m3u dosyasını yaz
    with open('r.m3u', 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_lines))

    print(f"\n✨ İşlem tamamlandı. Toplam {total_channels} kanal '{SAVE_FOLDER}' klasörüne ve 'r.m3u' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
