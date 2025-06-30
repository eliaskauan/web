# -*- coding: utf-8 -*-
"""
Processador de arquivos CSV para o sistema de web scraping
"""

import logging
import os
from typing import List, Tuple

import pandas as pd

from config import CSV_TERMO_COLUMN, CSV_RESULTADO_COLUMN


class CSVProcessor:
    """
    Classe responsável pelo processamento de arquivos CSV
    """
    
    def __init__(self, csv_path: str):
        """
        Inicializa o processador CSV
        
        Args:
            csv_path: Caminho para o arquivo CSV
        """
        self.csv_path = csv_path
        self.df = None
        self.logger = logging.getLogger(__name__)
        
        # Verificar se arquivo existe
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_path}")
    
    def carregar_csv(self) -> pd.DataFrame:
        """
        Carrega o arquivo CSV
        
        Returns:
            DataFrame do pandas
        """
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            self.logger.info(f"CSV carregado: {len(self.df)} linhas")
            
            # Verificar se coluna 'termo' existe
            if CSV_TERMO_COLUMN not in self.df.columns:
                raise ValueError(f"Coluna '{CSV_TERMO_COLUMN}' não encontrada no CSV")
            
            # Criar coluna 'resultado' se não existir
            if CSV_RESULTADO_COLUMN not in self.df.columns:
                self.df[CSV_RESULTADO_COLUMN] = ""
                self.logger.info(f"Coluna '{CSV_RESULTADO_COLUMN}' criada")
            
            return self.df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CSV: {e}")
            raise
    
    def obter_termos_pendentes(self) -> List[Tuple[int, str]]:
        """
        Obtém lista de termos que ainda não foram processados
        
        Returns:
            Lista de tuplas (índice, termo)
        """
        if self.df is None:
            self.carregar_csv()
        
        # Filtrar linhas onde resultado está vazio ou é NaN
        mask = (self.df[CSV_RESULTADO_COLUMN].isna()) | (self.df[CSV_RESULTADO_COLUMN] == "")
        linhas_pendentes = self.df[mask]
        
        termos = []
        for idx, row in linhas_pendentes.iterrows():
            termo = str(row[CSV_TERMO_COLUMN]).strip()
            if termo and termo.lower() != 'nan':
                termos.append((idx, termo))
        
        self.logger.info(f"Encontrados {len(termos)} termos pendentes para processar")
        return termos
    
    def atualizar_resultado(self, indice: int, status: str):
        """
        Atualiza o status de um termo no CSV
        
        Args:
            indice: Índice da linha no DataFrame
            status: Status a ser atualizado
        """
        try:
            if self.df is None:
                raise ValueError("CSV não foi carregado")
            
            self.df.at[indice, CSV_RESULTADO_COLUMN] = status
            self.logger.debug(f"Status atualizado para linha {indice}: {status}")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar resultado: {e}")
            raise
    
    def salvar_csv(self, backup: bool = True):
        """
        Salva o CSV atualizado
        
        Args:
            backup: Se True, cria backup do arquivo original
        """
        try:
            if self.df is None:
                raise ValueError("CSV não foi carregado")
            
            # Criar backup se solicitado
            if backup and os.path.exists(self.csv_path):
                backup_path = f"{self.csv_path}.backup"
                if not os.path.exists(backup_path):
                    import shutil
                    shutil.copy2(self.csv_path, backup_path)
                    self.logger.info(f"Backup criado: {backup_path}")
            
            # Salvar CSV atualizado
            self.df.to_csv(self.csv_path, index=False, encoding='utf-8')
            self.logger.info(f"CSV salvo: {self.csv_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")
            raise
    
    def obter_estatisticas(self) -> dict:
        """
        Obtém estatísticas do processamento
        
        Returns:
            Dicionário com estatísticas
        """
        if self.df is None:
            return {}
        
        total = len(self.df)
        processados = len(self.df[self.df[CSV_RESULTADO_COLUMN] != ""])
        pendentes = total - processados
        
        # Contar por status
        status_counts = self.df[CSV_RESULTADO_COLUMN].value_counts().to_dict()
        
        return {
            "total": total,
            "processados": processados,
            "pendentes": pendentes,
            "por_status": status_counts
        }
    
    def validar_csv(self) -> List[str]:
        """
        Valida a estrutura do CSV
        
        Returns:
            Lista de problemas encontrados
        """
        problemas = []
        
        try:
            if self.df is None:
                self.carregar_csv()
            
            # Verificar colunas obrigatórias
            if CSV_TERMO_COLUMN not in self.df.columns:
                problemas.append(f"Coluna '{CSV_TERMO_COLUMN}' não encontrada")
            
            # Verificar se há termos válidos
            if CSV_TERMO_COLUMN in self.df.columns:
                termos_validos = self.df[CSV_TERMO_COLUMN].dropna()
                termos_validos = termos_validos[termos_validos.astype(str).str.strip() != ""]
                
                if len(termos_validos) == 0:
                    problemas.append("Nenhum termo válido encontrado na coluna 'termo'")
            
            # Verificar se arquivo tem linhas
            if len(self.df) == 0:
                problemas.append("Arquivo CSV está vazio")
            
        except Exception as e:
            problemas.append(f"Erro ao validar CSV: {e}")
        
        return problemas