# -*- coding: utf-8 -*-
"""
Classe principal para web scraping do site Parts Unlimited
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

from config import (
    DEFAULT_DELAY_MIN, DEFAULT_DELAY_MAX, DEFAULT_TIMEOUT, MAX_RETRIES,
    BASE_URL, HOME_URL, SELECTORS,
    STATUS_OK, STATUS_NAO_ENCONTRADO, STATUS_ERRO
)


class WebScraper:
    """
    Classe responsável pelo web scraping do site Parts Unlimited
    """
    
    def __init__(self, headless: bool = True, debug: bool = False):
        """
        Inicializa o scraper
        
        Args:
            headless: Se True, executa o navegador em modo headless
            debug: Se True, ativa logs de debug
        """
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Configurar logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
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
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Criar contexto com configurações anti-detecção
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                ])
            )
            
            self.page = await context.new_page()
            
            # Configurar timeouts
            self.page.set_default_timeout(DEFAULT_TIMEOUT)
            
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
        delay = random.uniform(DEFAULT_DELAY_MIN, DEFAULT_DELAY_MAX)
        self.logger.debug(f"Aguardando {delay:.1f} segundos...")
        await asyncio.sleep(delay)
    
    async def buscar_termo(self, termo: str) -> Tuple[str, Optional[str]]:
        """
        Busca um termo no site através do campo de busca da página principal
        
        Args:
            termo: Termo a ser buscado
            
        Returns:
            Tupla (status, produto_url)
        """
        for tentativa in range(MAX_RETRIES):
            try:
                self.logger.info(f"Buscando termo: '{termo}' (tentativa {tentativa + 1})")
                
                # Navegar para página principal
                await self.page.goto(HOME_URL, wait_until="networkidle")
                await self.page.wait_for_load_state("networkidle")
                
                # Simular comportamento humano inicial
                await self.simular_comportamento_humano()
                
                # Encontrar campo de busca
                search_box = await self.encontrar_campo_busca()
                if not search_box:
                    self.logger.error("Campo de busca não encontrado na página")
                    if tentativa < MAX_RETRIES - 1:
                        await self.delay_aleatorio()
                        continue
                    return STATUS_ERRO, None
                
                # Limpar campo e inserir termo
                await search_box.click()  # Focar no campo
                await search_box.press("Control+a")  # Selecionar tudo
                await search_box.press("Delete")  # Deletar conteúdo
                await search_box.fill(termo)  # Inserir novo termo
                
                # Simular digitação humana
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Tentar submeter busca
                sucesso_busca = await self.submeter_busca(search_box)
                if not sucesso_busca:
                    self.logger.error("Falha ao submeter busca")
                    if tentativa < MAX_RETRIES - 1:
                        await self.delay_aleatorio()
                        continue
                    return STATUS_ERRO, None
                
                # Aguardar carregamento dos resultados
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Verificar se há resultados
                produto_url = await self.extrair_primeiro_produto()
                
                if produto_url:
                    self.logger.info(f"Produto encontrado para '{termo}': {produto_url}")
                    await self.delay_aleatorio()
                    return STATUS_OK, produto_url
                else:
                    self.logger.info(f"Nenhum produto encontrado para '{termo}'")
                    await self.delay_aleatorio()
                    return STATUS_NAO_ENCONTRADO, None
                    
            except PlaywrightTimeoutError:
                self.logger.warning(f"Timeout na busca de '{termo}' - tentativa {tentativa + 1}")
                if tentativa < MAX_RETRIES - 1:
                    await self.delay_aleatorio()
                    continue
            except Exception as e:
                self.logger.error(f"Erro na busca de '{termo}': {e}")
                if tentativa < MAX_RETRIES - 1:
                    await self.delay_aleatorio()
                    continue
        
        return STATUS_ERRO, None
    
    async def encontrar_campo_busca(self):
        """
        Encontra o campo de busca na página usando múltiplos seletores e XPath
        
        Returns:
            Elemento do campo de busca ou None se não encontrado
        """
        try:
            # Método 1: Tentar XPath específico primeiro
            try:
                search_box = await self.page.query_selector("xpath=//*[@id='search-input']")
                if search_box:
                    is_visible = await search_box.is_visible()
                    is_enabled = await search_box.is_enabled()
                    
                    if is_visible and is_enabled:
                        self.logger.debug("Campo de busca encontrado com XPath: //*[@id='search-input']")
                        return search_box
            except Exception as e:
                self.logger.debug(f"Erro ao tentar XPath específico: {e}")
            
            # Método 2: Tentar seletores CSS configurados
            for selector in SELECTORS["search_box"].split(", "):
                try:
                    search_box = await self.page.query_selector(selector.strip())
                    if search_box:
                        # Verificar se elemento está visível e habilitado
                        is_visible = await search_box.is_visible()
                        is_enabled = await search_box.is_enabled()
                        
                        if is_visible and is_enabled:
                            self.logger.debug(f"Campo de busca encontrado com selector: {selector}")
                            return search_box
                except Exception as e:
                    self.logger.debug(f"Erro ao tentar selector {selector}: {e}")
                    continue
            
            # Método 3: Tentar XPaths genéricos para busca
            xpath_selectors = [
                "xpath=//input[@id='search-input']",
                "xpath=//input[contains(@placeholder, 'search')]",
                "xpath=//input[contains(@placeholder, 'Search')]",
                "xpath=//input[contains(@name, 'search')]",
                "xpath=//input[contains(@name, 'q')]",
                "xpath=//input[@type='search']"
            ]
            
            for xpath in xpath_selectors:
                try:
                    search_box = await self.page.query_selector(xpath)
                    if search_box:
                        is_visible = await search_box.is_visible()
                        is_enabled = await search_box.is_enabled()
                        
                        if is_visible and is_enabled:
                            self.logger.debug(f"Campo de busca encontrado com XPath: {xpath}")
                            return search_box
                except Exception as e:
                    self.logger.debug(f"Erro ao tentar XPath {xpath}: {e}")
                    continue
            
            # Método 4: Seletores CSS genéricos
            generic_selectors = [
                "input[type='text']",
                "input[type='search']",
                "input:not([type='hidden']):not([type='submit'])",
                "*[placeholder*='search' i]",
                "*[name*='search' i]"
            ]
            
            for selector in generic_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            # Verificar se parece com campo de busca
                            placeholder = await element.get_attribute("placeholder") or ""
                            name = await element.get_attribute("name") or ""
                            id_attr = await element.get_attribute("id") or ""
                            
                            busca_keywords = ["search", "query", "q", "find", "lookup"]
                            texto_completo = f"{placeholder} {name} {id_attr}".lower()
                            
                            if any(keyword in texto_completo for keyword in busca_keywords):
                                self.logger.debug(f"Campo de busca encontrado genericamente: {selector}")
                                return element
                except Exception as e:
                    self.logger.debug(f"Erro na busca genérica {selector}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao encontrar campo de busca: {e}")
            return None
    
    async def submeter_busca(self, search_box):
        """
        Submete a busca através do campo encontrado
        
        Args:
            search_box: Elemento do campo de busca
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Método 1: Tentar pressionar Enter
            try:
                await search_box.press("Enter")
                await asyncio.sleep(1)
                self.logger.debug("Busca submetida com Enter")
                return True
            except Exception as e:
                self.logger.debug(f"Falha ao pressionar Enter: {e}")
            
            # Método 2: Procurar botão de busca próximo
            try:
                # Buscar botão de submit no mesmo formulário
                form = await search_box.evaluate("element => element.closest('form')")
                if form:
                    submit_button = await self.page.query_selector("form button[type='submit'], form input[type='submit']")
                    if submit_button:
                        await submit_button.click()
                        await asyncio.sleep(1)
                        self.logger.debug("Busca submetida via botão do formulário")
                        return True
            except Exception as e:
                self.logger.debug(f"Falha ao submeter via formulário: {e}")
            
            # Método 3: Procurar botão de busca por seletores
            try:
                for selector in SELECTORS["search_button"].split(", "):
                    button = await self.page.query_selector(selector.strip())
                    if button:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        
                        if is_visible and is_enabled:
                            await button.click()
                            await asyncio.sleep(1)
                            self.logger.debug(f"Busca submetida via botão: {selector}")
                            return True
            except Exception as e:
                self.logger.debug(f"Falha ao encontrar botão de busca: {e}")
            
            # Método 4: Tentar submeter formulário via JavaScript
            try:
                await search_box.evaluate("""
                    element => {
                        const form = element.closest('form');
                        if (form) {
                            form.submit();
                        }
                    }
                """)
                await asyncio.sleep(1)
                self.logger.debug("Busca submetida via JavaScript")
                return True
            except Exception as e:
                self.logger.debug(f"Falha ao submeter via JavaScript: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao submeter busca: {e}")
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
            
        except Exception as e:
            self.logger.debug(f"Erro ao simular comportamento humano: {e}")
    
    async def extrair_primeiro_produto(self) -> Optional[str]:
        """
        Extrai a URL do primeiro produto da página de resultados
        
        Returns:
            URL do produto ou None se não encontrado
        """
        try:
            # Aguardar elementos de resultado carregarem
            await asyncio.sleep(3)
            
            # Debug: listar elementos encontrados na página
            if self.debug:
                await self.debug_elementos_pagina()
            
            # Método 1: Tentar XPath específico primeiro  
            xpath_selectors = [
                "xpath=//*[@id='20101555']",
                "xpath=//*[@id='20101555']//a",
                "xpath=//*[@id='20101555']/div",
                "xpath=//*[@id='20101555']/div//a",
                "xpath=//*[contains(@id, '2010') and contains(@id, '1555')]",
                "xpath=//*[contains(@id, '2010')]//a",
                "xpath=//div[contains(@id, '2010')]//a",
                "xpath=//div[contains(@class, 'product')]",
                "xpath=//div[contains(@class, 'result')]//a",
                "xpath=//article//a",
                "xpath=//*[contains(@class, 'item')]//a"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elemento = await self.page.query_selector(xpath)
                    if elemento:
                        self.logger.debug(f"Produto encontrado com XPath: {xpath}")
                        
                        # Se o elemento já é um link
                        tag_name = await elemento.evaluate("element => element.tagName.toLowerCase()")
                        if tag_name == "a":
                            href = await elemento.get_attribute("href")
                            if href:
                                self.logger.info(f"Link direto encontrado: {href}")
                                return self.normalizar_url(href)
                        
                        # Se não é um link, procurar link dentro do elemento
                        link = await elemento.query_selector("a")
                        if link:
                            href = await link.get_attribute("href")
                            if href:
                                self.logger.info(f"Link encontrado dentro do elemento: {href}")
                                return self.normalizar_url(href)
                        
                        # Se ainda não encontrou link, tentar clicar no elemento
                        try:
                            is_clickable = await elemento.is_enabled()
                            if is_clickable:
                                self.logger.info("Elemento é clicável, tentando clicar...")
                                await elemento.click()
                                await self.page.wait_for_load_state("networkidle", timeout=10000)
                                current_url = self.page.url
                                if current_url != BASE_URL and "search" not in current_url:
                                    self.logger.info(f"Redirecionado para página do produto: {current_url}")
                                    return current_url
                        except Exception as e:
                            self.logger.debug(f"Erro ao tentar clicar no elemento: {e}")
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao tentar XPath {xpath}: {e}")
                    continue
            
            # Método 2: Tentar seletores CSS configurados
            for selector in SELECTORS["search_results"].split(", "):
                try:
                    elementos = await self.page.query_selector_all(selector.strip())
                    if elementos:
                        # Pegar o primeiro elemento
                        primeiro_elemento = elementos[0]
                        self.logger.debug(f"Elemento encontrado com selector: {selector}")
                        
                        # Procurar link dentro do elemento
                        link = await primeiro_elemento.query_selector("a")
                        if link:
                            href = await link.get_attribute("href")
                            if href:
                                self.logger.info(f"Link encontrado: {href}")
                                return self.normalizar_url(href)
                        
                        # Se não encontrou link, tentar clicar no elemento
                        try:
                            is_clickable = await primeiro_elemento.is_enabled()
                            if is_clickable:
                                self.logger.info("Tentando clicar no elemento produto...")
                                await primeiro_elemento.click()
                                await self.page.wait_for_load_state("networkidle", timeout=10000)
                                current_url = self.page.url
                                if current_url != BASE_URL and "search" not in current_url:
                                    self.logger.info(f"Redirecionado para: {current_url}")
                                    return current_url
                        except Exception as e:
                            self.logger.debug(f"Erro ao clicar no elemento: {e}")
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao tentar selector {selector}: {e}")
                    continue
            
            # Método 3: Busca genérica por links
            generic_selectors = [
                "a[href*='product']",
                "a[href*='item']",
                "a[href*='part']",
                "a[href*='/p/']",
                "a[onclick*='product']",
                "div[onclick*='product']"
            ]
            
            for selector in generic_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    if links:
                        href = await links[0].get_attribute("href")
                        if href:
                            self.logger.info(f"Link genérico encontrado: {href}")
                            return self.normalizar_url(href)
                except Exception as e:
                    self.logger.debug(f"Erro na busca genérica {selector}: {e}")
                    continue
            
            self.logger.warning("Nenhum produto encontrado nos resultados")
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
    
    async def debug_elementos_pagina(self):
        """Função de debug para listar elementos na página"""
        try:
            self.logger.debug("=== DEBUG: Elementos encontrados na página ===")
            
            # Listar todos os elementos com ID
            elementos_com_id = await self.page.query_selector_all("[id]")
            self.logger.debug(f"Elementos com ID: {len(elementos_com_id)}")
            
            for i, elemento in enumerate(elementos_com_id[:10]):  # Primeiros 10
                element_id = await elemento.get_attribute("id")
                tag_name = await elemento.evaluate("element => element.tagName.toLowerCase()")
                self.logger.debug(f"  {i+1}. <{tag_name}> id='{element_id}'")
            
            # Procurar especificamente pelo elemento do produto
            produto_elemento = await self.page.query_selector("#20101555")
            if produto_elemento:
                self.logger.debug("✅ Elemento #20101555 encontrado!")
                
                # Ver se tem links dentro
                links = await produto_elemento.query_selector_all("a")
                self.logger.debug(f"Links dentro do elemento: {len(links)}")
                
                for i, link in enumerate(links):
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    self.logger.debug(f"  Link {i+1}: href='{href}' text='{text[:50]}'")
                
                # Ver se é clicável
                is_clickable = await produto_elemento.is_enabled()
                is_visible = await produto_elemento.is_visible()
                self.logger.debug(f"Clicável: {is_clickable}, Visível: {is_visible}")
            else:
                self.logger.debug("❌ Elemento #20101555 NÃO encontrado")
                
        except Exception as e:
            self.logger.debug(f"Erro no debug: {e}")
    
    async def extrair_dados_produto(self, produto_url: str) -> Optional[Dict]:
        """
        Extrai todos os dados de um produto
        
        Args:
            produto_url: URL do produto
            
        Returns:
            Dicionário com dados do produto ou None se erro
        """
        for tentativa in range(MAX_RETRIES):
            try:
                self.logger.info(f"Extraindo dados do produto: {produto_url}")
                
                # Navegar para página do produto
                await self.page.goto(produto_url, wait_until="networkidle")
                await self.page.wait_for_load_state("networkidle")
                
                # Simular comportamento humano
                await self.simular_comportamento_humano()
                
                # Extrair dados
                dados = {
                    "url": produto_url,
                    "nome": await self.extrair_texto_seguro(SELECTORS["product_name"]),
                    "preco": await self.extrair_texto_seguro(SELECTORS["product_price"]),
                    "sku": await self.extrair_texto_seguro(SELECTORS["product_sku"]),
                    "imagens": await self.extrair_imagens(),
                    "descricao": await self.extrair_texto_seguro(SELECTORS["product_description"]),
                    "especificacoes": await self.extrair_especificacoes(),
                    "disponibilidade": await self.extrair_texto_seguro(SELECTORS["product_availability"]),
                    "categoria": await self.extrair_texto_seguro(SELECTORS["product_category"])
                }
                
                # Filtrar dados vazios
                dados = {k: v for k, v in dados.items() if v}
                
                self.logger.info(f"Dados extraídos com sucesso: {len(dados)} campos")
                await self.delay_aleatorio()
                return dados
                
            except Exception as e:
                self.logger.error(f"Erro ao extrair dados do produto (tentativa {tentativa + 1}): {e}")
                if tentativa < MAX_RETRIES - 1:
                    await self.delay_aleatorio()
                    continue
        
        return None
    
    async def extrair_texto_seguro(self, seletores: str) -> Optional[str]:
        """Extrai texto usando múltiplos seletores como fallback"""
        try:
            for selector in seletores.split(", "):
                try:
                    elemento = await self.page.query_selector(selector.strip())
                    if elemento:
                        texto = await elemento.inner_text()
                        if texto and texto.strip():
                            return texto.strip()
                except:
                    continue
            return None
        except Exception as e:
            self.logger.debug(f"Erro ao extrair texto: {e}")
            return None
    
    async def extrair_imagens(self) -> List[str]:
        """Extrai URLs de todas as imagens do produto"""
        try:
            imagens = []
            elementos_img = await self.page.query_selector_all(SELECTORS["product_images"])
            
            for img in elementos_img:
                src = await img.get_attribute("src")
                if src:
                    # Converter para URL absoluta se necessário
                    if src.startswith("/"):
                        src = urljoin(BASE_URL, src)
                    imagens.append(src)
            
            return list(set(imagens))  # Remover duplicatas
        except Exception as e:
            self.logger.debug(f"Erro ao extrair imagens: {e}")
            return []
    
    async def extrair_especificacoes(self) -> Dict[str, str]:
        """Extrai especificações técnicas do produto"""
        try:
            specs = {}
            elementos_specs = await self.page.query_selector_all(SELECTORS["product_specs"])
            
            for elemento in elementos_specs:
                texto = await elemento.inner_text()
                if texto:
                    # Tentar extrair pares chave-valor
                    linhas = texto.split('\n')
                    for linha in linhas:
                        if ':' in linha:
                            chave, valor = linha.split(':', 1)
                            specs[chave.strip()] = valor.strip()
            
            return specs
        except Exception as e:
            self.logger.debug(f"Erro ao extrair especificações: {e}")
            return {}