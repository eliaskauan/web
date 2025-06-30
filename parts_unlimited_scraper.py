# -*- coding: utf-8 -*-
"""
Sistema expandido de Web Scraping para Parts Unlimited com login e extração completa
"""

import asyncio
import logging
import random
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import time
import re

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from PIL import Image
import io

from config import (
    DEFAULT_DELAY_MIN, DEFAULT_DELAY_MAX, DEFAULT_TIMEOUT, MAX_RETRIES,
    BASE_URL, HOME_URL, SELECTORS,
    STATUS_OK, STATUS_NAO_ENCONTRADO, STATUS_ERRO
)


class PartsUnlimitedScraperAdvanced:
    """
    Classe avançada para web scraping do site Parts Unlimited com login e extração completa
    """
    
    def __init__(self, credenciais: Dict, configuracoes: Dict, headless: bool = True, debug: bool = False):
        """
        Inicializa o scraper avançado
        
        Args:
            credenciais: Dicionário com credenciais de login
            configuracoes: Dicionário com configurações
            headless: Se True, executa o navegador em modo headless
            debug: Se True, ativa logs de debug
        """
        self.credenciais = credenciais
        self.configuracoes = configuracoes
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logado = False
        self.tentativas_login = 0
        
        # Configurar logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Criar diretórios necessários
        self.diretorio_imagens = Path(configuracoes.get('diretorio_imagens', 'images/'))
        self.diretorio_videos = Path(configuracoes.get('diretorio_videos', 'videos/'))
        self.diretorio_imagens.mkdir(exist_ok=True)
        self.diretorio_videos.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """Context manager para inicializar o navegador"""
        await self.inicializar_navegador()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager para fechar o navegador"""
        await self.fechar_navegador()
    
    async def inicializar_navegador(self):
        """Inicializa o navegador Playwright"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Criar contexto com configurações anti-detecção
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = await context.new_page()
            
            # Configurar timeouts
            timeout = self.configuracoes.get('timeout', DEFAULT_TIMEOUT)
            self.page.set_default_timeout(timeout)
            
            self.logger.info("Navegador inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar navegador: {e}")
            raise
    
    async def fechar_navegador(self):
        """Fecha o navegador"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            self.logger.info("Navegador fechado")
        except Exception as e:
            self.logger.error(f"Erro ao fechar navegador: {e}")
    
    async def delay_aleatorio(self):
        """Aplica delay aleatório entre requisições"""
        delay_min = self.configuracoes.get('delay_min', DEFAULT_DELAY_MIN)
        delay_max = self.configuracoes.get('delay_max', DEFAULT_DELAY_MAX)
        delay = random.uniform(delay_min, delay_max)
        self.logger.debug(f"Aguardando {delay:.1f} segundos...")
        await asyncio.sleep(delay)
    
    async def fazer_login(self) -> bool:
        """
        Realiza login no site Parts Unlimited
        
        Returns:
            True se login foi bem-sucedido, False caso contrário
        """
        max_tentativas = 3
        
        for tentativa in range(max_tentativas):
            try:
                self.logger.info(f"Tentativa de login {tentativa + 1}/{max_tentativas}")
                
                # Navegar para página de login
                url_login = self.credenciais.get('url_login', f'{BASE_URL}/login')
                await self.page.goto(url_login, wait_until="networkidle")
                await self.page.wait_for_load_state("networkidle")
                
                # Simular comportamento humano
                await self.simular_comportamento_humano()
                
                # Encontrar campos de login
                username_field = await self.encontrar_campo_login('username')
                password_field = await self.encontrar_campo_login('password')
                
                if not username_field or not password_field:
                    self.logger.error("Campos de login não encontrados")
                    if tentativa < max_tentativas - 1:
                        await self.delay_aleatorio()
                        continue
                    return False
                
                # Preencher credenciais
                username = self.credenciais.get('username', '')
                password = self.credenciais.get('password', '')
                
                if not username or not password:
                    self.logger.error("Credenciais não fornecidas")
                    return False
                
                # Preencher campos
                await username_field.click()
                await username_field.fill('')
                await username_field.type(username, delay=random.randint(50, 150))
                
                await password_field.click()
                await password_field.fill('')
                await password_field.type(password, delay=random.randint(50, 150))
                
                # Aguardar um pouco
                await asyncio.sleep(random.uniform(1, 2))
                
                # Submeter login
                sucesso_login = await self.submeter_login()
                
                if sucesso_login:
                    # Verificar se login foi bem-sucedido
                    await asyncio.sleep(3)
                    
                    if await self.verificar_login_sucesso():
                        self.logger.info("Login realizado com sucesso!")
                        self.logado = True
                        return True
                    else:
                        self.logger.warning("Login aparentemente falhou - verificando novamente...")
                        if tentativa < max_tentativas - 1:
                            await self.delay_aleatorio()
                            continue
                
            except Exception as e:
                self.logger.error(f"Erro durante tentativa de login {tentativa + 1}: {e}")
                if tentativa < max_tentativas - 1:
                    await self.delay_aleatorio()
                    continue
        
        self.logger.error("Falha ao realizar login após todas as tentativas")
        return False
    
    async def encontrar_campo_login(self, tipo: str):
        """
        Encontra campo de login (username ou password)
        
        Args:
            tipo: 'username' ou 'password'
            
        Returns:
            Elemento do campo ou None
        """
        try:
            if tipo == 'username':
                seletores = self.credenciais.get('selector_username', 
                    '#username, input[name="username"], input[type="email"], input[name="email"]').split(', ')
            else:
                seletores = self.credenciais.get('selector_password',
                    '#password, input[name="password"], input[type="password"]').split(', ')
            
            for seletor in seletores:
                try:
                    element = await self.page.query_selector(seletor.strip())
                    if element:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            self.logger.debug(f"Campo {tipo} encontrado: {seletor}")
                            return element
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao encontrar campo {tipo}: {e}")
            return None
    
    async def submeter_login(self) -> bool:
        """Submete o formulário de login"""
        try:
            # Tentar encontrar botão de login
            seletores_botao = self.credenciais.get('selector_login_btn',
                'button[type="submit"], input[type="submit"], .login-btn, .btn-login').split(', ')
            
            for seletor in seletores_botao:
                try:
                    button = await self.page.query_selector(seletor.strip())
                    if button:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        
                        if is_visible and is_enabled:
                            await button.click()
                            self.logger.debug(f"Botão de login clicado: {seletor}")
                            return True
                except Exception:
                    continue
            
            # Se não encontrou botão, tentar Enter no campo password
            password_field = await self.encontrar_campo_login('password')
            if password_field:
                await password_field.press("Enter")
                self.logger.debug("Enter pressionado no campo password")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao submeter login: {e}")
            return False
    
    async def verificar_login_sucesso(self) -> bool:
        """Verifica se o login foi bem-sucedido"""
        try:
            # Verificar URL atual
            current_url = self.page.url
            
            # Se não estamos mais na página de login, provavelmente funcionou
            if 'login' not in current_url.lower():
                return True
            
            # Procurar indicadores de usuário logado
            indicadores_logado = [
                '.user-menu', '.account-menu', '.logout', '.sign-out',
                '[href*="logout"]', '[href*="account"]', '.user-name'
            ]
            
            for indicador in indicadores_logado:
                try:
                    elemento = await self.page.query_selector(indicador)
                    if elemento and await elemento.is_visible():
                        return True
                except Exception:
                    continue
            
            # Verificar se há mensagens de erro de login
            erros_login = [
                '.error', '.alert-danger', '.login-error', '.invalid'
            ]
            
            for seletor_erro in erros_login:
                try:
                    erro = await self.page.query_selector(seletor_erro)
                    if erro and await erro.is_visible():
                        mensagem = await erro.inner_text()
                        self.logger.warning(f"Possível erro de login: {mensagem}")
                        return False
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar login: {e}")
            return False
    
    async def simular_comportamento_humano(self):
        """Simula comportamento humano na página"""
        try:
            # Scroll aleatório
            scroll_distance = random.randint(100, 500)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            
            # Pequena pausa
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Movimento do mouse aleatório
            await self.page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            
            # Pequena pausa adicional
            await asyncio.sleep(random.uniform(0.2, 1.0))
            
        except Exception as e:
            self.logger.debug(f"Erro ao simular comportamento humano: {e}")
    
    async def buscar_produto(self, codigo_produto: str) -> Tuple[str, Optional[str]]:
        """
        Busca um produto no site
        
        Args:
            codigo_produto: Código do produto a ser buscado
            
        Returns:
            Tupla (status, produto_url)
        """
        max_tentativas = self.configuracoes.get('max_tentativas', MAX_RETRIES)
        
        for tentativa in range(max_tentativas):
            try:
                self.logger.info(f"Buscando produto: '{codigo_produto}' (tentativa {tentativa + 1})")
                
                # Navegar para página principal se não estivermos lá
                await self.page.goto(HOME_URL, wait_until="networkidle")
                await self.page.wait_for_load_state("networkidle")
                
                # Simular comportamento humano
                await self.simular_comportamento_humano()
                
                # Encontrar campo de busca
                search_box = await self.encontrar_campo_busca()
                if not search_box:
                    self.logger.error("Campo de busca não encontrado")
                    if tentativa < max_tentativas - 1:
                        await self.delay_aleatorio()
                        continue
                    return STATUS_ERRO, None
                
                # Limpar e preencher campo de busca
                await search_box.click()
                await search_box.press("Control+a")
                await search_box.press("Delete")
                await search_box.type(codigo_produto, delay=random.randint(50, 150))
                
                # Aguardar e submeter busca
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                if not await self.submeter_busca(search_box):
                    self.logger.error("Falha ao submeter busca")
                    if tentativa < max_tentativas - 1:
                        await self.delay_aleatorio()
                        continue
                    return STATUS_ERRO, None
                
                # Aguardar resultados
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Extrair primeiro produto
                produto_url = await self.extrair_primeiro_produto()
                
                if produto_url:
                    self.logger.info(f"Produto encontrado: {produto_url}")
                    await self.delay_aleatorio()
                    return STATUS_OK, produto_url
                else:
                    self.logger.info(f"Produto não encontrado: {codigo_produto}")
                    await self.delay_aleatorio()
                    return STATUS_NAO_ENCONTRADO, None
                    
            except Exception as e:
                self.logger.error(f"Erro na busca (tentativa {tentativa + 1}): {e}")
                if tentativa < max_tentativas - 1:
                    await self.delay_aleatorio()
                    continue
        
        return STATUS_ERRO, None
    
    async def encontrar_campo_busca(self):
        """Encontra o campo de busca na página"""
        try:
            seletores = [
                "#search-input",
                "input[type='search']",
                "input[name='q']",
                "input[placeholder*='search']",
                "input[placeholder*='Search']",
                ".search-input",
                "#search"
            ]
            
            for seletor in seletores:
                try:
                    element = await self.page.query_selector(seletor)
                    if element:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            self.logger.debug(f"Campo de busca encontrado: {seletor}")
                            return element
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao encontrar campo de busca: {e}")
            return None
    
    async def submeter_busca(self, search_box) -> bool:
        """Submete a busca"""
        try:
            # Tentar Enter primeiro
            await search_box.press("Enter")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            self.logger.debug(f"Erro ao submeter busca: {e}")
            return False
    
    async def extrair_primeiro_produto(self) -> Optional[str]:
        """Extrai URL do primeiro produto dos resultados"""
        try:
            await asyncio.sleep(3)
            
            # Seletores para produtos nos resultados
            seletores_produto = [
                "a[href*='product']",
                "a[href*='item']", 
                "a[href*='part']",
                ".product-item a",
                ".search-result a",
                ".product-card a"
            ]
            
            for seletor in seletores_produto:
                try:
                    links = await self.page.query_selector_all(seletor)
                    if links:
                        for link in links:
                            href = await link.get_attribute("href")
                            if href and href != '#':
                                return self.normalizar_url(href)
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair primeiro produto: {e}")
            return None
    
    def normalizar_url(self, url: str) -> str:
        """Normaliza URL para formato absoluto"""
        if url.startswith("/"):
            return urljoin(BASE_URL, url)
        elif not url.startswith("http"):
            return urljoin(BASE_URL, "/" + url)
        return url
    
    async def extrair_dados_produto_completos(self, produto_url: str, codigo_produto: str) -> Optional[Dict]:
        """
        Extrai todos os dados de um produto de forma completa
        
        Args:
            produto_url: URL do produto
            codigo_produto: Código do produto
            
        Returns:
            Dicionário com todos os dados do produto
        """
        try:
            self.logger.info(f"Extraindo dados completos do produto: {produto_url}")
            
            # Navegar para página do produto
            await self.page.goto(produto_url, wait_until="networkidle")
            await self.page.wait_for_load_state("networkidle")
            
            # Simular comportamento humano
            await self.simular_comportamento_humano()
            
            # Criar pasta específica para o produto
            pasta_produto = self.criar_pasta_produto(codigo_produto)
            
            # Extrair todos os dados
            dados = {
                'link_produto': produto_url,
                'descricao_titulo': await self.extrair_titulo(),
                'sub_descricao': await self.extrair_sub_titulo(),
                'features': await self.extrair_features(),
                'specs': await self.extrair_specs(),
                'part_codes': await self.extrair_part_codes(),
                'part_notices': await self.extrair_part_notices(),
                'certifications': await self.extrair_certifications(),
                'references': await self.extrair_references(),
                'package_info': await self.extrair_package_info(),
                'size_chart': await self.extrair_size_chart(),
                'video_url': await self.extrair_video_url(),
                'imagens_urls': await self.extrair_e_baixar_imagens(codigo_produto, pasta_produto),
                'substituicao_oem': await self.extrair_substituicao_oem(),
                'tabela_ajustes': await self.extrair_tabela_ajustes(),
                'texto_ajustes': await self.extrair_texto_ajustes(),
                'link_catalogo': await self.extrair_link_catalogo(),
                'imagem_diretorio': await self.extrair_imagem_diretorio(),
                'video_detalhado': await self.extrair_video_detalhado()
            }
            
            # Filtrar dados vazios
            dados_filtrados = {k: v for k, v in dados.items() if v}
            
            # Realizar auto-conferência
            problemas = self.validar_dados_extraidos(dados_filtrados)
            if problemas:
                self.logger.warning(f"Problemas encontrados na extração: {problemas}")
            
            self.logger.info(f"Extração completa finalizada: {len(dados_filtrados)} campos")
            await self.delay_aleatorio()
            
            return dados_filtrados
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados completos: {e}")
            return None
    
    def criar_pasta_produto(self, codigo_produto: str) -> Path:
        """Cria pasta específica para o produto"""
        try:
            # Sanitizar nome da pasta
            nome_pasta = re.sub(r'[<>:"/\\|?*]', '', str(codigo_produto))
            nome_pasta = re.sub(r'\s+', '_', nome_pasta.strip())
            
            pasta_produto = self.diretorio_imagens / nome_pasta
            pasta_produto.mkdir(exist_ok=True)
            
            return pasta_produto
            
        except Exception as e:
            self.logger.error(f"Erro ao criar pasta do produto: {e}")
            return self.diretorio_imagens
    
    async def extrair_titulo(self) -> str:
        """Extrai título principal do produto"""
        seletores = [
            "h1",
            ".product-title",
            ".product-name", 
            ".main-title",
            "[data-testid='product-title']"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_sub_titulo(self) -> str:
        """Extrai subtítulo do produto"""
        seletores = [
            "h2",
            ".product-subtitle",
            ".sub-title",
            ".product-description-short"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_features(self) -> str:
        """Extrai features do produto"""
        seletores = [
            ".features",
            ".product-features",
            ".feature-list",
            "[data-section='features']",
            ".highlights"
        ]
        
        # Tentar extrair como lista primeiro
        texto_features = await self.extrair_lista_por_seletores(seletores)
        if texto_features:
            return texto_features
        
        # Se não encontrar lista, tentar texto simples
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_specs(self) -> str:
        """Extrai especificações técnicas"""
        seletores = [
            ".specifications",
            ".specs",
            ".tech-specs",
            ".product-specs",
            "[data-section='specifications']",
            ".spec-table"
        ]
        
        # Tentar extrair tabela de especificações
        specs_tabela = await self.extrair_tabela_por_seletores(seletores)
        if specs_tabela:
            return specs_tabela
        
        # Se não encontrar tabela, tentar lista
        specs_lista = await self.extrair_lista_por_seletores(seletores)
        if specs_lista:
            return specs_lista
        
        # Se não encontrar lista, tentar texto simples
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_part_codes(self) -> str:
        """Extrai códigos das peças"""
        seletores = [
            ".part-codes",
            ".product-codes",
            ".sku-list",
            ".part-numbers"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_part_notices(self) -> str:
        """Extrai avisos das peças"""
        seletores = [
            ".part-notices",
            ".product-notices",
            ".warnings",
            ".important-info"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_certifications(self) -> str:
        """Extrai certificações"""
        seletores = [
            ".certifications",
            ".certificates",
            ".product-certifications"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_references(self) -> str:
        """Extrai referências (links)"""
        try:
            seletores = [
                ".references a",
                ".related-links a",
                ".external-links a"
            ]
            
            links = []
            for seletor in seletores:
                try:
                    elementos = await self.page.query_selector_all(seletor)
                    for elemento in elementos:
                        href = await elemento.get_attribute("href")
                        text = await elemento.inner_text()
                        if href and text:
                            links.append(f"{text.strip()}: {self.normalizar_url(href)}")
                except Exception:
                    continue
            
            return '; '.join(links) if links else ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair referências: {e}")
            return ''
    
    async def extrair_package_info(self) -> str:
        """Extrai informações de embalagem"""
        seletores = [
            ".package-info",
            ".packaging",
            ".shipping-info"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_size_chart(self) -> str:
        """Extrai tabela de tamanhos"""
        seletores = [
            ".size-chart",
            ".sizing-chart",
            ".dimensions"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_video_url(self) -> str:
        """Extrai URL de vídeo do produto"""
        try:
            seletores_video = [
                "video source",
                "iframe[src*='youtube']",
                "iframe[src*='vimeo']",
                "[data-video-url]"
            ]
            
            for seletor in seletores_video:
                try:
                    elemento = await self.page.query_selector(seletor)
                    if elemento:
                        src = await elemento.get_attribute("src")
                        if src:
                            return src
                        
                        data_url = await elemento.get_attribute("data-video-url")
                        if data_url:
                            return data_url
                except Exception:
                    continue
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair vídeo: {e}")
            return ''
    
    async def extrair_e_baixar_imagens(self, codigo_produto: str, pasta_produto: Path) -> str:
        """
        Extrai URLs das imagens e faz download para pasta local
        
        Args:
            codigo_produto: Código do produto
            pasta_produto: Pasta onde salvar as imagens
            
        Returns:
            String com URLs das imagens separadas por ;
        """
        try:
            seletores_imagem = [
                ".product-images img",
                ".gallery img",
                ".product-gallery img",
                ".image-gallery img",
                "[data-testid='product-image']"
            ]
            
            urls_imagens = []
            imagens_baixadas = []
            
            for seletor in seletores_imagem:
                try:
                    elementos = await self.page.query_selector_all(seletor)
                    for i, elemento in enumerate(elementos):
                        src = await elemento.get_attribute("src")
                        if src and src.startswith(('http', 'https')):
                            urls_imagens.append(src)
                            
                            # Baixar imagem
                            nome_arquivo = f"{codigo_produto}_{i+1}.jpg"
                            caminho_arquivo = pasta_produto / nome_arquivo
                            
                            if await self.baixar_imagem(src, caminho_arquivo):
                                imagens_baixadas.append(str(caminho_arquivo))
                                
                except Exception:
                    continue
            
            # Remover duplicatas
            urls_imagens = list(set(urls_imagens))
            
            self.logger.info(f"Imagens processadas: {len(urls_imagens)} encontradas, {len(imagens_baixadas)} baixadas")
            
            return '; '.join(urls_imagens)
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair imagens: {e}")
            return ''
    
    async def baixar_imagem(self, url: str, caminho_arquivo: Path) -> bool:
        """
        Baixa uma imagem da URL especificada
        
        Args:
            url: URL da imagem
            caminho_arquivo: Caminho onde salvar
            
        Returns:
            True se download foi bem-sucedido
        """
        try:
            # Evitar baixar se arquivo já existe
            if caminho_arquivo.exists():
                return True
            
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Verificar se é realmente uma imagem
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False
            
            # Salvar imagem
            with open(caminho_arquivo, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verificar se arquivo foi salvo corretamente
            if caminho_arquivo.exists() and caminho_arquivo.stat().st_size > 0:
                self.logger.debug(f"Imagem baixada: {caminho_arquivo}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Erro ao baixar imagem {url}: {e}")
            return False
    
    async def extrair_substituicao_oem(self) -> str:
        """Extrai informações de substituição OEM"""
        seletores = [
            ".oem-replacement",
            ".oem-info",
            ".replacement-parts"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_tabela_ajustes(self) -> str:
        """Extrai tabela de ajustes"""
        seletores = [
            ".fitment-table",
            ".compatibility-table",
            ".fits-table"
        ]
        
        return await self.extrair_tabela_por_seletores(seletores)
    
    async def extrair_texto_ajustes(self) -> str:
        """Extrai texto de ajustes"""
        seletores = [
            ".fitment-info",
            ".compatibility-info",
            ".fits-description"
        ]
        
        return await self.extrair_texto_por_seletores(seletores)
    
    async def extrair_link_catalogo(self) -> str:
        """Extrai link para catálogo"""
        try:
            seletores = [
                "a[href*='catalog']",
                "a[href*='manual']",
                ".catalog-link"
            ]
            
            for seletor in seletores:
                try:
                    elemento = await self.page.query_selector(seletor)
                    if elemento:
                        href = await elemento.get_attribute("href")
                        if href:
                            return self.normalizar_url(href)
                except Exception:
                    continue
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair link catálogo: {e}")
            return ''
    
    async def extrair_imagem_diretorio(self) -> str:
        """Extrai imagem do diretório"""
        seletores = [
            ".directory-image img",
            ".category-image img"
        ]
        
        try:
            for seletor in seletores:
                elemento = await self.page.query_selector(seletor)
                if elemento:
                    src = await elemento.get_attribute("src")
                    if src:
                        return self.normalizar_url(src)
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair imagem diretório: {e}")
            return ''
    
    async def extrair_video_detalhado(self) -> str:
        """Extrai vídeo detalhado da peça"""
        try:
            seletores = [
                ".detailed-video iframe",
                ".instruction-video iframe",
                "[data-detailed-video]"
            ]
            
            for seletor in seletores:
                elemento = await self.page.query_selector(seletor)
                if elemento:
                    src = await elemento.get_attribute("src")
                    if src:
                        return src
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair vídeo detalhado: {e}")
            return ''
    
    # Métodos auxiliares para extração
    
    async def extrair_texto_por_seletores(self, seletores: List[str]) -> str:
        """Extrai texto usando lista de seletores"""
        try:
            for seletor in seletores:
                try:
                    elemento = await self.page.query_selector(seletor)
                    if elemento:
                        texto = await elemento.inner_text()
                        if texto and texto.strip():
                            return texto.strip()
                except Exception:
                    continue
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair texto: {e}")
            return ''
    
    async def extrair_lista_por_seletores(self, seletores: List[str]) -> str:
        """Extrai lista de itens usando seletores"""
        try:
            for seletor in seletores:
                try:
                    # Tentar listas ul/ol primeiro
                    lista = await self.page.query_selector(f"{seletor} ul, {seletor} ol")
                    if lista:
                        items = await lista.query_selector_all("li")
                        textos = []
                        for item in items:
                            texto = await item.inner_text()
                            if texto and texto.strip():
                                textos.append(texto.strip())
                        
                        if textos:
                            return '\n• ' + '\n• '.join(textos)
                    
                    # Se não encontrar lista, tentar elementos filhos
                    container = await self.page.query_selector(seletor)
                    if container:
                        elementos = await container.query_selector_all("div, p, span")
                        textos = []
                        for elemento in elementos:
                            texto = await elemento.inner_text()
                            if texto and texto.strip() and len(texto.strip()) > 3:
                                textos.append(texto.strip())
                        
                        if textos:
                            return '\n• ' + '\n• '.join(textos)
                            
                except Exception:
                    continue
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair lista: {e}")
            return ''
    
    async def extrair_tabela_por_seletores(self, seletores: List[str]) -> str:
        """Extrai dados de tabela usando seletores"""
        try:
            for seletor in seletores:
                try:
                    tabela = await self.page.query_selector(f"{seletor} table, {seletor}")
                    if tabela:
                        # Verificar se é uma tabela
                        tag_name = await tabela.evaluate("element => element.tagName.toLowerCase()")
                        
                        if tag_name == 'table':
                            linhas = await tabela.query_selector_all("tr")
                            dados_tabela = []
                            
                            for linha in linhas:
                                celulas = await linha.query_selector_all("td, th")
                                dados_linha = []
                                
                                for celula in celulas:
                                    texto = await celula.inner_text()
                                    if texto:
                                        dados_linha.append(texto.strip())
                                
                                if dados_linha:
                                    dados_tabela.append(' | '.join(dados_linha))
                            
                            if dados_tabela:
                                return '\n'.join(dados_tabela)
                        
                        # Se não for tabela, tentar extrair como texto estruturado
                        texto = await tabela.inner_text()
                        if texto and texto.strip():
                            return texto.strip()
                            
                except Exception:
                    continue
            
            return ''
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair tabela: {e}")
            return ''
    
    def validar_dados_extraidos(self, dados: Dict) -> List[str]:
        """
        Valida os dados extraídos (auto-conferência)
        
        Args:
            dados: Dados extraídos
            
        Returns:
            Lista de problemas encontrados
        """
        problemas = []
        
        try:
            # Verificar campos obrigatórios
            if not dados.get('link_produto'):
                problemas.append("Link do produto não encontrado")
            
            if not dados.get('descricao_titulo'):
                problemas.append("Título do produto não encontrado")
            
            # Verificar se pelo menos alguns campos importantes foram preenchidos
            campos_importantes = ['features', 'specs', 'imagens_urls']
            campos_preenchidos = sum(1 for campo in campos_importantes if dados.get(campo))
            
            if campos_preenchidos == 0:
                problemas.append("Nenhum campo importante foi preenchido (features, specs, imagens)")
            
            # Verificar formato de URLs
            campos_url = ['link_produto', 'video_url', 'link_catalogo']
            for campo in campos_url:
                url = dados.get(campo)
                if url and not url.startswith(('http://', 'https://')):
                    problemas.append(f"URL inválida no campo {campo}: {url}")
            
            # Verificar se imagens foram encontradas
            imagens = dados.get('imagens_urls', '')
            if imagens:
                urls_imagens = [url.strip() for url in imagens.split(';') if url.strip()]
                if len(urls_imagens) == 0:
                    problemas.append("URLs de imagens estão em formato inválido")
            
        except Exception as e:
            problemas.append(f"Erro durante validação: {e}")
        
        return problemas