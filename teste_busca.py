#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar a busca no campo específico
"""

import asyncio
import logging
from web_scraper import WebScraper

async def testar_busca():
    """Teste simples da funcionalidade de busca"""
    
    logging.basicConfig(level=logging.DEBUG)
    
    async with WebScraper(headless=False, debug=True) as scraper:
        print("Testando busca com termo: 2010-1555")
        
        status, produto_url = await scraper.buscar_termo("2010-1555")
        
        print(f"Status: {status}")
        print(f"URL do produto: {produto_url}")
        
        if status == "OK" and produto_url:
            print("Extraindo dados do produto...")
            dados = await scraper.extrair_dados_produto(produto_url)
            
            if dados:
                print("Dados extraídos:")
                for chave, valor in dados.items():
                    print(f"  {chave}: {valor}")
            else:
                print("Falha ao extrair dados")

if __name__ == "__main__":
    asyncio.run(testar_busca())