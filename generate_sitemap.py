import os
import datetime
import urllib.parse

BASE_URL = "https://testedprofit.com/"
EXCLUDED_DIRS = {'.git', '.github', 'src', 'verification'}

def generate_sitemap():
    urls = []

    # Walk the directory tree
    for root, dirs, files in os.walk('.'):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]

        if 'index.html' in files:
            # Construct the URL path
            rel_path = os.path.relpath(root, '.')

            if rel_path == '.':
                url_path = ''
                priority = '1.00'
            else:
                # Replace backslashes with forward slashes for cross-platform compatibility
                # URL encode path components to handle spaces and special characters
                parts = rel_path.split(os.sep)
                parts = [urllib.parse.quote(p) for p in parts]
                url_path = '/'.join(parts) + '/'
                priority = '0.80'

            full_url = BASE_URL + url_path
            lastmod = datetime.date.today().isoformat()

            urls.append({
                'loc': full_url,
                'lastmod': lastmod,
                'priority': priority
            })

    # Sort URLs for consistent output
    urls.sort(key=lambda x: x['loc'])

    # Generate XML content
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                       'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                       'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 '
                       'http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">')
    xml_content.append('<!-- created with generate_sitemap.py -->')

    for url in urls:
        xml_content.append('<url>')
        xml_content.append(f'  <loc>{url["loc"]}</loc>')
        xml_content.append(f'  <lastmod>{url["lastmod"]}</lastmod>')
        xml_content.append(f'  <priority>{url["priority"]}</priority>')
        xml_content.append('</url>')

    xml_content.append('</urlset>')

    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_content))

    print(f"Sitemap generated with {len(urls)} URLs.")

if __name__ == "__main__":
    generate_sitemap()
