#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests
from urllib.parse import urljoin

# ==================== AYARLAR ====================
DEFAULT_MAIN_URL = 'https://m.prectv60.lol'
DEFAULT_SW_KEY = '4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452/'
DEFAULT_USER_AGENT = 'okhttp/4.12.0/'
DEFAULT_REFERER = 'https://twitter.com/'
PAGE_COUNT = 4

M3U_USER_AGENT = 'googleusercontent'
OUTPUT_DIR = 'rec'

# ==================== YARDIMCI ====================
def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.strip('_')

# ==================== ANA İŞLEV ====================
def create_channel_files(main_url, sw_key, user_agent, referer):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    headers = {
        'User-Agent': user_agent,
        'Referer': referer
    }

    total_channels = 0

    for page in range(PAGE_COUNT):
        api_url = f"{main_url}/api/channel/by/filtres/0/0/{page}/{sw_key}"

        try:
            r = requests.get(api_url, headers=headers, timeout=20, verify=False)
            if r.status_code != 200:
                continue

            data = r.json()
            if not isinstance(data, list):
                continue

            for content in data:
                title = content.get('title', '').strip()
                if not title:
                    continue

                categories = ''
                if isinstance(content.get('categories'), list):
                    categories = ', '.join(c.get('title', '') for c in content['categories'])

                # SADECE SPOR
                if categories != "Spor":
                    continue

                for src in content.get('sources', []):
                    if src.get('type') != 'm3u8':
                        continue

                    stream_url = src.get('url')
                    if not stream_url:
                        continue

                    filename = safe_filename(title) + '.m3u8'
                    filepath = os.path.join(OUTPUT_DIR, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('#EXTM3U\n')
                        f.write(f'#EXTINF:-1,{title}\n')
                        f.write(f'#EXTVLCOPT:http-user-agent={M3U_USER_AGENT}\n')
                        f.write(f'#EXTVLCOPT:http-referrer={referer}\n')
                        f.write(stream_url + '\n')

                    total_channels += 1
                    print(f"Oluşturuldu: {filepath}")

        except Exception as e:
            print(f"Hata (sayfa {page}): {e}")

    print(f"\nToplam {total_channels} adet kanal dosyası oluşturuldu.")

# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    create_channel_files(
        DEFAULT_MAIN_URL,
        DEFAULT_SW_KEY,
        DEFAULT_USER_AGENT,
        DEFAULT_REFERER
    )
