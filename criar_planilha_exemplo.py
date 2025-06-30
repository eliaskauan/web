#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar planilha Excel de exemplo para teste do scraper
"""

from pathlib import Path
from excel_processor import ExcelProcessor


def criar_planilha_exemplo():
    """Cria uma planilha Excel de exemplo com dados de teste"""
    
    caminho_exemplo = Path("exemplo_produtos.xlsx")
    
    # Criar processador (que criará a planilha padrão)
    excel_processor = ExcelProcessor(str(caminho_exemplo))
    
    # Adicionar alguns códigos de produto de exemplo
    produtos_exemplo = [
        "20101555",
        "20101556", 
        "20101557",
        "ABC123",
        "XYZ789"
    ]
    
    # Preencher produtos na planilha
    for i, codigo in enumerate(produtos_exemplo, 2):  # Começar na linha 2
        excel_processor.sheet_produtos[f'A{i}'].value = codigo
    
    # Preencher credenciais de exemplo
    excel_processor.sheet_credenciais['B4'].value = 'seu_usuario_aqui'
    excel_processor.sheet_credenciais['B5'].value = 'sua_senha_aqui'
    
    # Salvar planilha
    excel_processor.salvar_excel(backup=False)
    
    print(f"✅ Planilha de exemplo criada: {caminho_exemplo}")
    print("\n📋 Para usar:")
    print("1. Abra o arquivo exemplo_produtos.xlsx")
    print("2. Preencha suas credenciais na aba 'Credenciais'")
    print("3. Adicione mais códigos de produtos na aba 'Produtos' se desejar")
    print("4. Execute: python main_scraper.py --excel exemplo_produtos.xlsx")


if __name__ == "__main__":
    criar_planilha_exemplo()