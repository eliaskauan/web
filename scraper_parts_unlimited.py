#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Web Scraping para Parts Unlimited
Extrai informações de produtos do site Parts Unlimited baseado em arquivo CSV
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

from csv_processor import CSVProcessor
from data_saver import DataSaver
from web_scraper import WebScraper
from config import OUTPUT_DIR, LOG_FILE, LOG_FORMAT


class PartsUnlimitedScraper:
    """
    Classe principal que orquestra todo o processo de scraping
    """
    
    def __init__(self, csv_path: str, output_dir: str = OUTPUT_DIR, headless: bool = True, debug: bool = False):
        """
        Inicializa o scraper principal
        
        Args:
            csv_path: Caminho para arquivo CSV de entrada
            output_dir: Diretório de saída para arquivos JSON
            headless: Se True, executa navegador em modo headless
            debug: Se True, ativa logs de debug
        """
        self.csv_path = csv_path
        self.output_dir = output_dir
        self.headless = headless
        self.debug = debug
        
        # Configurar logging
        self.configurar_logging()
        self.logger = logging.getLogger(__name__)
        
        # Inicializar componentes
        self.csv_processor = CSVProcessor(csv_path)
        self.data_saver = DataSaver(output_dir)
        
        # Estatísticas
        self.stats = {
            "total": 0,
            "processados": 0,
            "encontrados": 0,
            "nao_encontrados": 0,
            "erros": 0,
            "inicio": None,
            "fim": None
        }
    
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
    
    async def executar(self):
        """Executa o processo completo de scraping"""
        try:
            self.stats["inicio"] = datetime.now()
            self.logger.info("=== INICIANDO SCRAPING PARTS UNLIMITED ===")
            
            # Validar entrada
            await self.validar_entrada()
            
            # Carregar CSV
            self.logger.info("Carregando arquivo CSV...")
            self.csv_processor.carregar_csv()
            
            # Obter termos pendentes
            termos_pendentes = self.csv_processor.obter_termos_pendentes()
            self.stats["total"] = len(termos_pendentes)
            
            if not termos_pendentes:
                self.logger.info("Nenhum termo pendente para processar")
                return
            
            self.logger.info(f"Processando {len(termos_pendentes)} termos...")
            
            # Inicializar web scraper
            async with WebScraper(headless=self.headless, debug=self.debug) as scraper:
                
                # Processar cada termo
                for i, (indice, termo) in enumerate(termos_pendentes, 1):
                    try:
                        self.logger.info(f"[{i}/{len(termos_pendentes)}] Processando: '{termo}'")
                        
                        # Buscar termo
                        status, produto_url = await scraper.buscar_termo(termo)
                        
                        # Atualizar CSV com status
                        self.csv_processor.atualizar_resultado(indice, status)
                        
                        if status == "OK" and produto_url:
                            # Extrair dados do produto
                            dados_produto = await scraper.extrair_dados_produto(produto_url)
                            
                            if dados_produto:
                                # Validar dados
                                problemas = self.data_saver.validar_dados_produto(dados_produto)
                                if problemas:
                                    self.logger.warning(f"Problemas nos dados do produto: {problemas}")
                                
                                # Salvar produto
                                arquivo_salvo = self.data_saver.salvar_produto(dados_produto)
                                self.logger.info(f"Produto salvo: {arquivo_salvo}")
                                self.stats["encontrados"] += 1
                            else:
                                self.logger.error(f"Falha ao extrair dados do produto: {produto_url}")
                                self.csv_processor.atualizar_resultado(indice, "erro")
                                self.stats["erros"] += 1
                        
                        elif status == "nao-encontrado":
                            self.stats["nao_encontrados"] += 1
                        
                        else:
                            self.stats["erros"] += 1
                        
                        self.stats["processados"] += 1
                        
                        # Salvar progresso a cada 5 produtos
                        if i % 5 == 0:
                            self.csv_processor.salvar_csv()
                            self.logger.info(f"Progresso salvo: {i}/{len(termos_pendentes)}")
                    
                    except Exception as e:
                        self.logger.error(f"Erro ao processar termo '{termo}': {e}")
                        self.csv_processor.atualizar_resultado(indice, "erro")
                        self.stats["erros"] += 1
                        self.stats["processados"] += 1
            
            # Salvar CSV final
            self.csv_processor.salvar_csv()
            
            # Estatísticas finais
            self.stats["fim"] = datetime.now()
            await self.exibir_estatisticas()
            
        except Exception as e:
            self.logger.error(f"Erro durante execução: {e}")
            raise
    
    async def validar_entrada(self):
        """Valida arquivos e configurações de entrada"""
        self.logger.info("Validando entrada...")
        
        # Validar CSV
        problemas_csv = self.csv_processor.validar_csv()
        if problemas_csv:
            for problema in problemas_csv:
                self.logger.error(f"Problema no CSV: {problema}")
            raise ValueError("CSV inválido")
        
        # Criar diretório de saída
        self.data_saver.criar_diretorio_saida()
        
        self.logger.info("Validação concluída com sucesso")
    
    async def exibir_estatisticas(self):
        """Exibe estatísticas finais do processamento"""
        duracao = self.stats["fim"] - self.stats["inicio"]
        
        self.logger.info("=== ESTATÍSTICAS FINAIS ===")
        self.logger.info(f"Total de termos: {self.stats['total']}")
        self.logger.info(f"Processados: {self.stats['processados']}")
        self.logger.info(f"Encontrados: {self.stats['encontrados']}")
        self.logger.info(f"Não encontrados: {self.stats['nao_encontrados']}")
        self.logger.info(f"Erros: {self.stats['erros']}")
        self.logger.info(f"Duração: {duracao}")
        
        # Estatísticas do CSV
        stats_csv = self.csv_processor.obter_estatisticas()
        self.logger.info(f"CSV - Total: {stats_csv.get('total', 0)}")
        self.logger.info(f"CSV - Processados: {stats_csv.get('processados', 0)}")
        self.logger.info(f"CSV - Pendentes: {stats_csv.get('pendentes', 0)}")
        
        # Estatísticas de saída
        stats_saida = self.data_saver.obter_estatisticas_saida()
        self.logger.info(f"Arquivos JSON criados: {stats_saida.get('total_produtos', 0)}")
        self.logger.info(f"Tamanho total: {stats_saida.get('tamanho_total_mb', 0)} MB")
        
        # Taxa de sucesso
        if self.stats['processados'] > 0:
            taxa_sucesso = (self.stats['encontrados'] / self.stats['processados']) * 100
            self.logger.info(f"Taxa de sucesso: {taxa_sucesso:.1f}%")


def main():
    """Função principal do programa"""
    parser = argparse.ArgumentParser(
        description="Sistema de Web Scraping para Parts Unlimited",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scraper_parts_unlimited.py --csv produtos.csv
  python scraper_parts_unlimited.py --csv dados.csv --output resultados/
  python scraper_parts_unlimited.py --csv lista.csv --debug --no-headless
        """
    )
    
    parser.add_argument(
        "--csv",
        required=True,
        help="Caminho para o arquivo CSV de entrada (obrigatório)"
    )
    
    parser.add_argument(
        "--output",
        default=OUTPUT_DIR,
        help=f"Diretório de saída para arquivos JSON (padrão: {OUTPUT_DIR})"
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
        version="Parts Unlimited Scraper v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Verificar se arquivo CSV existe
    if not os.path.exists(args.csv):
        print(f"Erro: Arquivo CSV não encontrado: {args.csv}")
        sys.exit(1)
    
    try:
        # Criar e executar scraper
        scraper = PartsUnlimitedScraper(
            csv_path=args.csv,
            output_dir=args.output,
            headless=not args.no_headless,
            debug=args.debug
        )
        
        # Executar scraping
        asyncio.run(scraper.executar())
        
        print("\n✅ Scraping concluído com sucesso!")
        print(f"📁 Resultados salvos em: {args.output}")
        print(f"📋 CSV atualizado: {args.csv}")
        print(f"📄 Log detalhado: {LOG_FILE}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()