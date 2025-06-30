# -*- coding: utf-8 -*-
"""
Sistema de salvamento de dados em JSON
"""

import json
import logging
import os
import re
from typing import Dict

from config import OUTPUT_DIR


class DataSaver:
    """
    Classe responsável pelo salvamento de dados dos produtos
    """
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        """
        Inicializa o salvador de dados
        
        Args:
            output_dir: Diretório de saída para os arquivos JSON
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Criar diretório de saída se não existir
        self.criar_diretorio_saida()
    
    def criar_diretorio_saida(self):
        """Cria o diretório de saída se não existir"""
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                self.logger.info(f"Diretório de saída criado: {self.output_dir}")
            else:
                self.logger.debug(f"Diretório de saída já existe: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Erro ao criar diretório de saída: {e}")
            raise
    
    def sanitizar_nome_arquivo(self, nome: str) -> str:
        """
        Sanitiza o nome do arquivo removendo caracteres inválidos
        
        Args:
            nome: Nome original
            
        Returns:
            Nome sanitizado
        """
        # Remover caracteres especiais e espaços
        nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
        nome_limpo = re.sub(r'\s+', '_', nome_limpo.strip())
        
        # Limitar tamanho do nome
        if len(nome_limpo) > 100:
            nome_limpo = nome_limpo[:100]
        
        # Garantir que não está vazio
        if not nome_limpo:
            nome_limpo = "produto_sem_codigo"
        
        return nome_limpo
    
    def extrair_codigo_produto(self, dados: Dict) -> str:
        """
        Extrai o código do produto dos dados para usar como nome do arquivo
        
        Args:
            dados: Dados do produto
            
        Returns:
            Código do produto sanitizado
        """
        # Tentar diferentes campos que podem conter o código
        campos_codigo = ['sku', 'codigo', 'product_code', 'id', 'item_number']
        
        for campo in campos_codigo:
            if campo in dados and dados[campo]:
                codigo = str(dados[campo]).strip()
                if codigo:
                    return self.sanitizar_nome_arquivo(codigo)
        
        # Se não encontrar código, tentar extrair da URL
        if 'url' in dados and dados['url']:
            url_parts = dados['url'].split('/')
            for part in reversed(url_parts):
                if part and not part.startswith('http'):
                    return self.sanitizar_nome_arquivo(part)
        
        # Se não encontrar código, tentar usar nome do produto
        if 'nome' in dados and dados['nome']:
            nome = str(dados['nome']).strip()
            if nome:
                return self.sanitizar_nome_arquivo(nome)
        
        # Último recurso: usar timestamp
        import time
        return f"produto_{int(time.time())}"
    
    def salvar_produto(self, dados: Dict) -> str:
        """
        Salva os dados do produto em arquivo JSON
        
        Args:
            dados: Dados do produto
            
        Returns:
            Caminho do arquivo salvo
        """
        try:
            # Extrair código do produto para nome do arquivo
            codigo_produto = self.extrair_codigo_produto(dados)
            nome_arquivo = f"{codigo_produto}.json"
            caminho_arquivo = os.path.join(self.output_dir, nome_arquivo)
            
            # Verificar se arquivo já existe e criar nome único se necessário
            contador = 1
            caminho_original = caminho_arquivo
            while os.path.exists(caminho_arquivo):
                nome_base = f"{codigo_produto}_{contador}.json"
                caminho_arquivo = os.path.join(self.output_dir, nome_base)
                contador += 1
            
            # Adicionar metadados
            dados_completos = {
                "metadados": {
                    "timestamp": self.obter_timestamp(),
                    "versao_scraper": "1.0.0",
                    "arquivo_origem": codigo_produto
                },
                "produto": dados
            }
            
            # Salvar arquivo JSON
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Produto salvo: {caminho_arquivo}")
            return caminho_arquivo
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar produto: {e}")
            raise
    
    def obter_timestamp(self) -> str:
        """Obtém timestamp atual formatado"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def verificar_produto_existe(self, codigo_produto: str) -> bool:
        """
        Verifica se um produto já foi salvo
        
        Args:
            codigo_produto: Código do produto
            
        Returns:
            True se produto já existe
        """
        codigo_sanitizado = self.sanitizar_nome_arquivo(codigo_produto)
        nome_arquivo = f"{codigo_sanitizado}.json"
        caminho_arquivo = os.path.join(self.output_dir, nome_arquivo)
        
        return os.path.exists(caminho_arquivo)
    
    def listar_produtos_salvos(self) -> list:
        """
        Lista todos os produtos salvos
        
        Returns:
            Lista de nomes de arquivos JSON
        """
        try:
            if not os.path.exists(self.output_dir):
                return []
            
            arquivos = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
            return sorted(arquivos)
            
        except Exception as e:
            self.logger.error(f"Erro ao listar produtos salvos: {e}")
            return []
    
    def obter_estatisticas_saida(self) -> dict:
        """
        Obtém estatísticas dos arquivos de saída
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            produtos_salvos = self.listar_produtos_salvos()
            total_arquivos = len(produtos_salvos)
            
            # Calcular tamanho total
            tamanho_total = 0
            if os.path.exists(self.output_dir):
                for arquivo in produtos_salvos:
                    caminho = os.path.join(self.output_dir, arquivo)
                    if os.path.exists(caminho):
                        tamanho_total += os.path.getsize(caminho)
            
            return {
                "total_produtos": total_arquivos,
                "tamanho_total_mb": round(tamanho_total / (1024 * 1024), 2),
                "diretorio_saida": self.output_dir,
                "arquivos": produtos_salvos[:10]  # Primeiros 10 para exemplo
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def validar_dados_produto(self, dados: Dict) -> list:
        """
        Valida os dados do produto antes de salvar
        
        Args:
            dados: Dados do produto
            
        Returns:
            Lista de problemas encontrados
        """
        problemas = []
        
        try:
            # Verificar se dados não estão vazios
            if not dados:
                problemas.append("Dados do produto estão vazios")
                return problemas
            
            # Verificar campos mínimos obrigatórios
            campos_obrigatorios = ['url']
            for campo in campos_obrigatorios:
                if campo not in dados or not dados[campo]:
                    problemas.append(f"Campo obrigatório '{campo}' não encontrado ou vazio")
            
            # Verificar se há pelo menos um campo útil além da URL
            campos_uteis = ['nome', 'preco', 'sku', 'descricao']
            tem_campo_util = any(campo in dados and dados[campo] for campo in campos_uteis)
            
            if not tem_campo_util:
                problemas.append("Nenhum campo útil encontrado (nome, preço, SKU ou descrição)")
            
            # Verificar formato de URLs de imagens
            if 'imagens' in dados and isinstance(dados['imagens'], list):
                for i, img_url in enumerate(dados['imagens']):
                    if not isinstance(img_url, str) or not img_url.startswith(('http', 'https')):
                        problemas.append(f"URL de imagem inválida na posição {i}: {img_url}")
            
        except Exception as e:
            problemas.append(f"Erro ao validar dados: {e}")
        
        return problemas