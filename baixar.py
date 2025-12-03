import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

visited = set()

def save_file(url, base_url, output_folder):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        # Caminho relativo dentro da pasta
        parsed = urlparse(url)
        path = parsed.path

        if path.endswith("/") or path == "":
            path += "index.html"

        file_path = os.path.join(output_folder, path.lstrip("/"))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"[+] Baixado: {url} → {file_path}")

        return response.content

    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return None


def crawl(url, base_url, output_folder):
    if url in visited:
        return
    visited.add(url)

    content = save_file(url, base_url, output_folder)
    if not content:
        return

    # Só analisa HTML
    if not url.endswith(".html") and not url.endswith("/"):
        return

    soup = BeautifulSoup(content, "html.parser")

    # Tags que podem conter arquivos
    tags = {
        "a": "href",
        "link": "href",
        "script": "src",
        "img": "src"
    }

    for tag, attr in tags.items():
        for element in soup.find_all(tag):
            file_url = element.get(attr)
            if not file_url:
                continue

            # Converte relativo para absoluto
            file_url = urljoin(url, file_url)

            # Só segue dentro do mesmo domínio
            if urlparse(file_url).netloc == urlparse(base_url).netloc:
                crawl(file_url, base_url, output_folder)


if __name__ == "__main__":
    start_url = "https://useipush.vendizap.com/"
    output_folder = "site_baixado"

    crawl(start_url, start_url, output_folder)
    print("\n✓ Finalizado! Arquivos salvos em:", output_folder)
