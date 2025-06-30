# -*- coding: utf-8 -*-
"""
Configurações do sistema de web scraping Parts Unlimited
"""

import random

# Configurações gerais
DEFAULT_DELAY_MIN = 2  # segundos
DEFAULT_DELAY_MAX = 8  # segundos
DEFAULT_TIMEOUT = 30000  # millisegundos
MAX_RETRIES = 3

# URLs do site
BASE_URL = "https://www.parts-unlimited.com"
HOME_URL = "https://www.parts-unlimited.com/"

# User agents rotativos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Headers HTTP variados
def get_random_headers():
    """Retorna headers HTTP aleatórios para evitar detecção"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

# Configurações de logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "scraper.log"

# Configurações de saída
OUTPUT_DIR = "saida"
CSV_RESULTADO_COLUMN = "resultado"
CSV_TERMO_COLUMN = "termo"

# Status de resultado
STATUS_OK = "OK"
STATUS_NAO_ENCONTRADO = "nao-encontrado"
STATUS_ERRO = "erro"

# Seletores CSS expandidos (podem precisar ser ajustados conforme o site)
SELECTORS = {
    "search_box": "#search-input, input[type='search'], #search, .search-input, input[name='q'], input[placeholder*='search'], input[placeholder*='Search']",
    "search_button": "button[type='submit'], .search-btn, .search-button, input[type='submit']",
    "search_results": "#20101555, .product-item, .search-result-item, [data-testid='product-card'], .product-card, .search-product, [id*='2010'], [id*='1555']",
    "product_link": "a[href*='/product/'], a[href*='/item/'], a[href*='/p/'], a",
    "product_name": "h1, .product-title, .product-name, .product-heading",
    "product_price": ".price, .product-price, [data-testid='price'], .cost, .amount",
    "product_sku": ".sku, .product-code, [data-testid='sku'], .part-number, .item-number",
    "product_images": "img[src*='product'], .product-image img, .gallery img, .product-photo img",
    "product_description": ".description, .product-description, .product-details, .product-info",
    "product_specs": ".specifications, .specs, .product-specs, .tech-specs",
    "product_availability": ".availability, .stock, .in-stock, .stock-status",
    "product_category": ".breadcrumb, .category, .product-category, .nav-path",
    
    # Seletores expandidos para extração completa
    "login_username": "#username, input[name='username'], input[type='email'], input[name='email']",
    "login_password": "#password, input[name='password'], input[type='password']",
    "login_button": "button[type='submit'], input[type='submit'], .login-btn, .btn-login",
    "features": ".features, .product-features, .feature-list, [data-section='features'], .highlights",
    "part_codes": ".part-codes, .product-codes, .sku-list, .part-numbers",
    "part_notices": ".part-notices, .product-notices, .warnings, .important-info",
    "certifications": ".certifications, .certificates, .product-certifications",
    "references": ".references a, .related-links a, .external-links a",
    "package_info": ".package-info, .packaging, .shipping-info",
    "size_chart": ".size-chart, .sizing-chart, .dimensions",
    "video": "video source, iframe[src*='youtube'], iframe[src*='vimeo'], [data-video-url]",
    "oem_replacement": ".oem-replacement, .oem-info, .replacement-parts",
    "fitment_table": ".fitment-table, .compatibility-table, .fits-table",
    "fitment_text": ".fitment-info, .compatibility-info, .fits-description",
    "catalog_link": "a[href*='catalog'], a[href*='manual'], .catalog-link",
    "directory_image": ".directory-image img, .category-image img",
    "detailed_video": ".detailed-video iframe, .instruction-video iframe, [data-detailed-video]"
}

# Configurações de diretórios
IMAGES_DIR = "images"
VIDEOS_DIR = "videos"
BACKUP_DIR = "backups"

# Configurações de download
DOWNLOAD_TIMEOUT = 30  # segundos
MAX_IMAGE_SIZE_MB = 50  # MB
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

# Configurações de auto-conferência
CAMPOS_OBRIGATORIOS = ['link_produto', 'descricao_titulo']
CAMPOS_IMPORTANTES = ['features', 'specs', 'imagens_urls']
MIN_CAMPOS_IMPORTANTES = 1