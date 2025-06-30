#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Principal de Web Scraping para Parts Unlimited
Versão expandida com login automático e extração completa de dados
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from excel_processor import ExcelProcessor
from parts_unlimited_scraper import PartsUnlimitedScraperAdvanced
from config import OUTPUT_DIR, LOG_FILE, LOG_FORMAT


class PartsUnlimitedScraperMain:
    """
    Classe principal que coordena todo o processo de scraping expandido
    """
    
    def __init__(self, excel_path: str, output_dir: str = OUTPUT_DIR, debug: bool = False):
        """
        Inicializa o scraper principal
        
        Args:
            excel_path: Caminho para arquivo Excel
            output_dir: Diretório de saída
            debug: Se True, ativa logs de debug
        """
        self.excel_path = excel_path
        self.output_dir = Path(output_dir)
        self.debug = debug
        
        # Configurar logging
        self.configurar_logging()
        self.logger = logging.getLogger(__name__)
        
        # Inicializar processador Excel
        self.excel_processor = ExcelProcessor(excel_path)
        
        # Obter configurações do Excel
        self.credenciais = self.excel_processor.obter_credenciais()
        self.configuracoes = self.excel_processor.obter_configuracoes()
        
        # Estatísticas
        self.stats = {
            "total": 0,
            "processados": 0,
            "encontrados": 0,
            "nao_encontrados": 0,
            "erros": 0,
            "login_sucesso": False,
            "inicio": None,
            "fim": None
        }
        
        # Criar diretório de saída
        self.output_dir.mkdir(exist_ok=True)
    
    def configurar_logging(self):
        """Configura o sistema de logging"""
        log_level = logging.DEBUG if self.debug else logging.INFO
        
        # Configurar logger principal
        logging.basicConfig(
            level=log_level,
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Reduzir verbosidade de bibliotecas externas
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("playwright").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)
    
    async def executar(self):
        """Executa o processo completo de scraping"""
        try:
            self.stats["inicio"] = datetime.now()
            self.logger.info("=== INICIANDO SCRAPING PARTS UNLIMITED EXPANDIDO ===")
            
            # Validar entrada
            await self.validar_entrada()
            
            # Obter produtos pendentes
            produtos_pendentes = self.excel_processor.obter_produtos_pendentes()
            self.stats["total"] = len(produtos_pendentes)
            
            if not produtos_pendentes:
                self.logger.info("Nenhum produto pendente para processar")
                return
            
            self.logger.info(f"Processando {len(produtos_pendentes)} produtos...")
            
            # Exibir configurações
            self.exibir_configuracoes()
            
            # Inicializar scraper avançado
            headless = self.configuracoes.get('headless', True)
            
            async with PartsUnlimitedScraperAdvanced(
                credenciais=self.credenciais,
                configuracoes=self.configuracoes,
                headless=headless,
                debug=self.debug
            ) as scraper:
                
                # Realizar login
                if await self.realizar_login(scraper):
                    self.stats["login_sucesso"] = True
                    
                    # Processar cada produto
                    await self.processar_produtos(scraper, produtos_pendentes)
                else:
                    self.logger.error("Falha no login - encerrando execução")
                    return
            
            # Salvar Excel final
            self.excel_processor.salvar_excel()
            
            # Estatísticas finais
            self.stats["fim"] = datetime.now()
            await self.exibir_estatisticas()
            
        except Exception as e:
            self.logger.error(f"Erro durante execução: {e}")
            raise
    
    async def validar_entrada(self):
        """Valida arquivos e configurações de entrada"""
        self.logger.info("Validando entrada...")
        
        # Validar Excel
        problemas_excel = self.excel_processor.validar_excel()
        if problemas_excel:
            for problema in problemas_excel:
                self.logger.error(f"Problema no Excel: {problema}")
            raise ValueError("Arquivo Excel inválido")
        
        # Verificar credenciais
        if not self.credenciais.get('username') or not self.credenciais.get('password'):
            self.logger.warning("Credenciais não fornecidas - tentativa sem login")
        
        self.logger.info("Validação concluída com sucesso")
    
    def exibir_configuracoes(self):
        """Exibe configurações atuais"""
        self.logger.info("=== CONFIGURAÇÕES ===")
        self.logger.info(f"Arquivo Excel: {self.excel_path}")
        self.logger.info(f"Diretório saída: {self.output_dir}")
        self.logger.info(f"Modo headless: {self.configuracoes.get('headless', True)}")
        self.logger.info(f"Debug: {self.debug}")
        self.logger.info(f"Delay: {self.configuracoes.get('delay_min', 2)}-{self.configuracoes.get('delay_max', 8)}s")
        self.logger.info(f"Max tentativas: {self.configuracoes.get('max_tentativas', 3)}")
        self.logger.info(f"Salvar a cada: {self.configuracoes.get('salvar_cada_n', 5)} produtos")
        self.logger.info(f"Usuário login: {self.credenciais.get('username', 'N/A')}")
    
    async def realizar_login(self, scraper) -> bool:
        """
        Realiza login no site
        
        Args:
            scraper: Instância do scraper
            
        Returns:
            True se login foi bem-sucedido
        """
        try:
            if not self.credenciais.get('username') or not self.credenciais.get('password'):
                self.logger.warning("Credenciais não fornecidas - continuando sem login")
                return True
            
            self.logger.info("Realizando login...")
            
            sucesso = await scraper.fazer_login()
            
            if sucesso:
                self.logger.info("✅ Login realizado com sucesso!")
                return True
            else:
                self.logger.error("❌ Falha no login após todas as tentativas")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro durante login: {e}")
            return False
    
    async def processar_produtos(self, scraper, produtos_pendentes):
        """
        Processa lista de produtos
        
        Args:
            scraper: Instância do scraper
            produtos_pendentes: Lista de produtos para processar
        """
        salvar_cada_n = self.configuracoes.get('salvar_cada_n', 5)
        
        for i, (linha, codigo_produto) in enumerate(produtos_pendentes, 1):
            try:
                self.logger.info(f"[{i}/{len(produtos_pendentes)}] Processando: '{codigo_produto}'")
                
                # Buscar produto
                status, produto_url = await scraper.buscar_produto(codigo_produto)
                
                if status == "OK" and produto_url:
                    # Extrair dados completos do produto
                    dados_produto = await scraper.extrair_dados_produto_completos(produto_url, codigo_produto)
                    
                    if dados_produto:
                        # Atualizar Excel com dados
                        self.excel_processor.atualizar_produto(linha, dados_produto)
                        self.logger.info(f"✅ Produto processado com sucesso: {codigo_produto}")
                        self.stats["encontrados"] += 1
                    else:
                        self.logger.error(f"❌ Falha ao extrair dados do produto: {codigo_produto}")
                        self.excel_processor.marcar_produto_erro(linha, "Falha na extração de dados")
                        self.stats["erros"] += 1
                
                elif status == "nao-encontrado":
                    self.excel_processor.marcar_produto_nao_encontrado(linha)
                    self.logger.info(f"⚠️ Produto não encontrado: {codigo_produto}")
                    self.stats["nao_encontrados"] += 1
                
                else:
                    self.excel_processor.marcar_produto_erro(linha, "Erro na busca")
                    self.logger.error(f"❌ Erro ao buscar produto: {codigo_produto}")
                    self.stats["erros"] += 1
                
                self.stats["processados"] += 1
                
                # Salvar progresso periodicamente
                if i % salvar_cada_n == 0:
                    self.excel_processor.salvar_excel()
                    self.logger.info(f"💾 Progresso salvo: {i}/{len(produtos_pendentes)}")
                    
                    # Exibir estatísticas parciais
                    self.exibir_progresso(i, len(produtos_pendentes))
            
            except Exception as e:
                self.logger.error(f"Erro ao processar produto '{codigo_produto}': {e}")
                self.excel_processor.marcar_produto_erro(linha, f"Erro: {str(e)[:100]}")
                self.stats["erros"] += 1
                self.stats["processados"] += 1
    
    def exibir_progresso(self, atual: int, total: int):
        """Exibe progresso atual"""
        percentual = (atual / total) * 100
        self.logger.info(f"📊 Progresso: {atual}/{total} ({percentual:.1f}%)")
        self.logger.info(f"✅ Encontrados: {self.stats['encontrados']}")
        self.logger.info(f"⚠️ Não encontrados: {self.stats['nao_encontrados']}")
        self.logger.info(f"❌ Erros: {self.stats['erros']}")
    
    async def exibir_estatisticas(self):
        """Exibe estatísticas finais do processamento"""
        duracao = self.stats["fim"] - self.stats["inicio"]
        
        self.logger.info("=== ESTATÍSTICAS FINAIS ===")
        self.logger.info(f"Total de produtos: {self.stats['total']}")
        self.logger.info(f"Processados: {self.stats['processados']}")
        self.logger.info(f"✅ Encontrados: {self.stats['encontrados']}")
        self.logger.info(f"⚠️ Não encontrados: {self.stats['nao_encontrados']}")
        self.logger.info(f"❌ Erros: {self.stats['erros']}")
        self.logger.info(f"Login realizado: {'✅ Sim' if self.stats['login_sucesso'] else '❌ Não'}")
        self.logger.info(f"Duração: {duracao}")
        
        # Estatísticas do Excel
        stats_excel = self.excel_processor.obter_estatisticas()
        self.logger.info(f"Excel - Total: {stats_excel.get('total', 0)}")
        self.logger.info(f"Excel - Concluídos: {stats_excel.get('concluidos', 0)}")
        self.logger.info(f"Excel - Pendentes: {stats_excel.get('pendentes', 0)}")
        
        # Taxa de sucesso
        if self.stats['processados'] > 0:
            taxa_sucesso = (self.stats['encontrados'] / self.stats['processados']) * 100
            self.logger.info(f"Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        # Informações de arquivos
        self.logger.info(f"Planilha atualizada: {self.excel_path}")
        self.logger.info(f"Imagens salvas em: {self.configuracoes.get('diretorio_imagens', 'images/')}")
        self.logger.info(f"Log detalhado: {LOG_FILE}")


def main():
    """Função principal do programa"""
    parser = argparse.ArgumentParser(
        description="Sistema Expandido de Web Scraping para Parts Unlimited",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main_scraper.py --excel produtos.xlsx
  python main_scraper.py --excel dados.xlsx --output resultados/
  python main_scraper.py --excel lista.xlsx --debug --no-headless

Estrutura da planilha Excel:
  - Aba 'Produtos': Lista de códigos de produtos na coluna A
  - Aba 'Credenciais': Login e senha para o site
  - Aba 'Configuracoes': Parâmetros do scraper

O sistema criará automaticamente:
  - Pastas para cada produto com imagens baixadas
  - Backup da planilha antes de salvar
  - Log detalhado de todas as operações
        """
    )
    
    parser.add_argument(
        "--excel",
        required=True,
        help="Caminho para o arquivo Excel de entrada (obrigatório)"
    )
    
    parser.add_argument(
        "--output",
        default=OUTPUT_DIR,
        help=f"Diretório base de saída (padrão: {OUTPUT_DIR})"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Executar navegador em modo visual (útil para debug)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativar modo debug com logs detalhados"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Parts Unlimited Scraper Expandido v2.0.0"
    )
    
    args = parser.parse_args()
    
    # Verificar se arquivo Excel existe
    if not os.path.exists(args.excel):
        print(f"❌ Erro: Arquivo Excel não encontrado: {args.excel}")
        sys.exit(1)
    
    try:
        # Criar e executar scraper
        scraper = PartsUnlimitedScraperMain(
            excel_path=args.excel,
            output_dir=args.output,
            debug=args.debug
        )
        
        # Executar scraping
        print("🚀 Iniciando scraping expandido...")
        asyncio.run(scraper.executar())
        
        print("\n✅ Scraping concluído com sucesso!")
        print(f"📁 Resultados salvos em: {args.output}")
        print(f"📋 Planilha atualizada: {args.excel}")
        print(f"📄 Log detalhado: {LOG_FILE}")
        print("\n📋 Verifique a planilha Excel para ver todos os dados coletados!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        print(f"📄 Verifique o log para mais detalhes: {LOG_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()