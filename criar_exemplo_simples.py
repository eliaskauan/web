#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para criar exemplo sem dependências externas
Cria arquivos CSV que podem ser importados no Excel
"""

import csv
import json
from pathlib import Path


def criar_aba_produtos():
    """Cria arquivo CSV para aba de produtos"""
    
    cabecalhos = [
        'Código do Produto',
        'Link do Produto', 
        'Descrição Título',
        'Sub Descrição',
        'Features',
        'Specs',
        'Part Codes',
        'Part Notices',
        'Certifications',
        'References',
        'Package Info',
        'Size Chart',
        'Vídeo URL',
        'Imagens URLs',
        'Substituição OEM',
        'Tabela Ajustes',
        'Texto Ajustes',
        'Link Catálogo',
        'Imagem Diretório',
        'Vídeo Detalhado',
        'Status',
        'Data Processamento',
        'Observações'
    ]
    
    # Produtos de exemplo
    produtos_exemplo = [
        ['20101555', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['20101556', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['20101557', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['ABC123', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['XYZ789', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
    ]
    
    with open('produtos.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(cabecalhos)
        writer.writerows(produtos_exemplo)
    
    print("✅ Arquivo 'produtos.csv' criado")


def criar_aba_credenciais():
    """Cria arquivo CSV para aba de credenciais"""
    
    credenciais = [
        ['Configuração', 'Valor'],
        ['URL Login', 'https://www.parts-unlimited.com/login'],
        ['Username', 'seu_usuario_aqui'],
        ['Password', 'sua_senha_aqui'],
        ['', ''],
        ['Seletores CSS', ''],
        ['Campo Username', '#username, input[name="username"], input[type="email"]'],
        ['Campo Password', '#password, input[name="password"], input[type="password"]'],
        ['Botão Login', 'button[type="submit"], input[type="submit"], .login-btn']
    ]
    
    with open('credenciais.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(credenciais)
    
    print("✅ Arquivo 'credenciais.csv' criado")


def criar_aba_configuracoes():
    """Cria arquivo CSV para aba de configurações"""
    
    configuracoes = [
        ['Configuração', 'Valor'],
        ['Diretório Imagens', 'images/'],
        ['Diretório Vídeos', 'videos/'],
        ['Delay Mínimo (seg)', '2'],
        ['Delay Máximo (seg)', '8'],
        ['Max Tentativas', '3'],
        ['Timeout (ms)', '30000'],
        ['Salvar a cada N produtos', '5'],
        ['Criar backup', 'SIM'],
        ['Modo Headless', 'SIM'],
        ['Debug', 'NAO']
    ]
    
    with open('configuracoes.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(configuracoes)
    
    print("✅ Arquivo 'configuracoes.csv' criado")


def criar_json_configuracao():
    """Cria arquivo JSON com configurações para o sistema"""
    
    config = {
        "credenciais": {
            "url_login": "https://www.parts-unlimited.com/login",
            "username": "seu_usuario_aqui",
            "password": "sua_senha_aqui",
            "selector_username": "#username, input[name=\"username\"], input[type=\"email\"]",
            "selector_password": "#password, input[name=\"password\"], input[type=\"password\"]",
            "selector_login_btn": "button[type=\"submit\"], input[type=\"submit\"], .login-btn"
        },
        "configuracoes": {
            "diretorio_imagens": "images/",
            "diretorio_videos": "videos/",
            "delay_min": 2,
            "delay_max": 8,
            "max_tentativas": 3,
            "timeout": 30000,
            "salvar_cada_n": 5,
            "criar_backup": True,
            "headless": True,
            "debug": False
        },
        "produtos": [
            "20101555",
            "20101556", 
            "20101557",
            "ABC123",
            "XYZ789"
        ]
    }
    
    with open('config_scraper.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("✅ Arquivo 'config_scraper.json' criado")


def criar_instrucoes():
    """Cria arquivo com instruções de uso"""
    
    instrucoes = """
# INSTRUÇÕES DE USO - Sistema de Scraping Parts Unlimited

## Arquivos Criados:

1. **produtos.csv** - Lista de produtos para processar
2. **credenciais.csv** - Configurações de login  
3. **configuracoes.csv** - Parâmetros do scraper
4. **config_scraper.json** - Configuração em formato JSON

## Como Usar:

### Opção 1: Com Excel (Recomendado)
1. Abra o Excel ou LibreOffice Calc
2. Importe os 3 arquivos CSV como abas separadas:
   - produtos.csv → Aba "Produtos"
   - credenciais.csv → Aba "Credenciais" 
   - configuracoes.csv → Aba "Configuracoes"
3. Salve como arquivo Excel (.xlsx)
4. Preencha suas credenciais na aba "Credenciais"
5. Execute: python main_scraper.py --excel arquivo.xlsx

### Opção 2: Sem Excel (Alternativa)
1. Edite o arquivo config_scraper.json
2. Preencha username e password
3. Adicione códigos de produtos na lista "produtos"
4. Use um script adaptado que leia JSON ao invés de Excel

### Opção 3: Instalar openpyxl
1. Execute: pip install openpyxl
2. Execute: python criar_planilha_exemplo.py
3. Isso criará um arquivo Excel completo automaticamente

## Próximos Passos:

1. **Configurar credenciais** nos arquivos criados
2. **Instalar dependências**: pip install playwright pandas openpyxl requests beautifulsoup4 pillow
3. **Instalar navegador**: playwright install chromium
4. **Executar scraper**: python main_scraper.py --excel seu_arquivo.xlsx

## Exemplo de Produtos:
- 20101555, 20101556, 20101557 (códigos de exemplo)
- ABC123, XYZ789 (códigos genéricos)

Substitua pelos códigos reais dos produtos que deseja processar.

## Estrutura Final:
Após execução, você terá:
- Planilha atualizada com todos os dados coletados
- Pasta images/ com imagens organizadas por produto
- Logs detalhados da execução
- Backups automáticos da planilha

🚀 Sistema pronto para uso!
"""
    
    with open('INSTRUCOES_USO.txt', 'w', encoding='utf-8') as f:
        f.write(instrucoes)
    
    print("✅ Arquivo 'INSTRUCOES_USO.txt' criado")


def main():
    """Função principal"""
    
    print("🚀 Criando arquivos de exemplo para o sistema de scraping...")
    print("=" * 60)
    
    # Criar todos os arquivos
    criar_aba_produtos()
    criar_aba_credenciais() 
    criar_aba_configuracoes()
    criar_json_configuracao()
    criar_instrucoes()
    
    print("\n🎉 ARQUIVOS DE EXEMPLO CRIADOS COM SUCESSO!")
    print("=" * 60)
    
    print("\n📁 Arquivos criados:")
    arquivos = [
        "produtos.csv - Lista de produtos para processar",
        "credenciais.csv - Configurações de login",
        "configuracoes.csv - Parâmetros do scraper", 
        "config_scraper.json - Configuração completa em JSON",
        "INSTRUCOES_USO.txt - Instruções detalhadas"
    ]
    
    for arquivo in arquivos:
        print(f"   ✅ {arquivo}")
    
    print("\n🔧 PRÓXIMOS PASSOS:")
    print("1. Edite 'credenciais.csv' e preencha seu usuário/senha")
    print("2. Importe os CSVs no Excel como abas separadas")
    print("3. Ou edite 'config_scraper.json' diretamente")
    print("4. Instale as dependências: pip install openpyxl playwright pandas")
    print("5. Execute: python main_scraper.py --excel seu_arquivo.xlsx")
    
    print("\n💡 Para mais detalhes, leia 'INSTRUCOES_USO.txt'")


if __name__ == "__main__":
    main()