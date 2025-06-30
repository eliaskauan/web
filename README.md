# Sistema de Web Scraping Parts Unlimited

Sistema completo de web scraping para extrair informações de produtos do site Parts Unlimited baseado em arquivo CSV.

## 🎯 Funcionalidades

- **Processamento CSV**: Lê arquivo CSV e busca produtos baseado na coluna "termo"
- **Busca Inteligente**: Utiliza o campo de busca da página principal para realizar pesquisas naturais
- **Extração Completa**: Extrai nome, preço, SKU, imagens, especificações e mais
- **Anti-Detecção**: Múltiplas estratégias para evitar bloqueios (user-agents, delays, etc.)
- **Salvamento JSON**: Organiza dados extraídos em arquivos JSON estruturados
- **Tratamento de Erros**: Sistema robusto com retry automático e logging detalhado
- **Progresso Incremental**: Salva progresso automaticamente para retomar execução

## 📦 Instalação

1. **Clone ou baixe os arquivos do projeto**

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Instale os navegadores do Playwright:**
```bash
playwright install chromium
```

## 🚀 Uso

### **Arquivo Principal: `main_scraper.py`**

### Uso Básico
```bash
python main_scraper.py --excel arquivo_entrada.xlsx
```

### Uso Avançado
```bash
# Especificar diretório de saída
python main_scraper.py --excel produtos.xlsx --output resultados/

# Modo debug com navegador visível
python main_scraper.py --excel dados.xlsx --debug --no-headless

# Ver ajuda completa
python main_scraper.py --help
```

### Outros arquivos disponíveis:
- `main_scraper_simples.py` - Versão de demonstração (usa config_scraper.json)
- `scraper_parts_unlimited.py` - Sistema para arquivos CSV

## 📁 Estrutura do Projeto

```
web-crawler/
├── main_scraper.py           # 🚀 ARQUIVO PRINCIPAL - Sistema completo com Excel
├── main_scraper_simples.py   # Versão de demonstração
├── scraper_parts_unlimited.py # Sistema para arquivos CSV
├── parts_unlimited_scraper.py # Classe de scraping avançada
├── web_scraper.py            # Classe de web scraping básica
├── csv_processor.py          # Processamento de CSV
├── excel_processor.py        # Processamento de Excel
├── data_saver.py            # Salvamento de dados
├── config.py                # Configurações para CSV
├── config_scraper.json      # Configurações para demonstração
├── requirements.txt         # Dependências
├── README.md               # Documentação
└── saida/                  # Diretório de arquivos JSON (criado automaticamente)
```

## 📄 Formato do CSV de Entrada

O arquivo CSV deve conter pelo menos uma coluna chamada `termo`:

```csv
termo,resultado
ABC123,
XYZ789,
DEF456,
```

- **termo**: Código ou termo a ser buscado
- **resultado**: Coluna atualizada automaticamente com status (OK, nao-encontrado, erro)

## 📊 Saída do Sistema

### 1. CSV Atualizado
O arquivo CSV original é atualizado com a coluna "resultado":
```csv
termo,resultado
ABC123,OK
XYZ789,nao-encontrado
DEF456,erro
```

### 2. Arquivos JSON
Para cada produto encontrado, um arquivo JSON é criado em `saida/`:

```json
{
  "metadados": {
    "timestamp": "2024-01-15T10:30:00",
    "versao_scraper": "1.0.0",
    "arquivo_origem": "ABC123"
  },
  "produto": {
    "url": "https://www.parts-unlimited.com/product/abc123",
    "nome": "Nome do Produto",
    "preco": "$99.99",
    "sku": "ABC123",
    "imagens": ["https://example.com/image1.jpg"],
    "descricao": "Descrição do produto...",
    "especificacoes": {
      "Material": "Alumínio",
      "Peso": "2.5 kg"
    },
    "disponibilidade": "Em estoque",
    "categoria": "Categoria > Subcategoria"
  }
}
```

### 3. Log Detalhado
Arquivo `scraper.log` com informações detalhadas da execução.

## ⚙️ Configurações

O arquivo `config.py` permite ajustar:

- **Delays**: Tempo entre requisições (2-8 segundos por padrão)
- **Timeouts**: Tempo limite para carregamento de páginas
- **User Agents**: Lista de user agents rotativos
- **Seletores CSS**: Seletores para extrair dados do site
- **Retries**: Número máximo de tentativas por produto

## 🛡️ Estratégias Anti-Detecção

- **User-agents rotativos**: Simula diferentes navegadores
- **Headers HTTP variados**: Headers realistas e convincentes
- **Delays aleatórios**: Entre 2-8 segundos por requisição
- **Simulação humana**: Scroll e movimentos de mouse
- **Rate limiting**: Controle inteligente de velocidade
- **Retry automático**: Recuperação de falhas temporárias

## 📈 Estatísticas

O sistema exibe estatísticas completas ao final:

```
=== ESTATÍSTICAS FINAIS ===
Total de termos: 100
Processados: 95
Encontrados: 78
Não encontrados: 12
Erros: 5
Taxa de sucesso: 82.1%
Duração: 0:15:30
```

## 🔧 Solução de Problemas

### Erro: "Arquivo CSV não encontrado"
- Verifique se o caminho do arquivo está correto
- Use caminho absoluto se necessário

### Erro: "Coluna 'termo' não encontrada"
- Certifique-se que o CSV tem uma coluna chamada "termo"
- Verifique a codificação do arquivo (deve ser UTF-8)

### Navegador não abre ou trava
- Tente executar com `--no-headless` para ver o navegador
- Verifique se o Playwright foi instalado corretamente
- Execute `playwright install chromium`

### Site está bloqueando requisições
- Aumente os delays em `config.py`
- Verifique se há captchas ou medidas anti-bot
- Use `--debug` para ver logs detalhados

### Produtos não são encontrados
- Verifique se os termos de busca estão corretos
- Use `--debug` para ver URLs de busca
- Os seletores CSS podem precisar de ajuste

## 📝 Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Sistema**: Windows, macOS ou Linux
- **Memória**: Mínimo 4GB RAM recomendado
- **Espaço**: ~500MB para Playwright + dados

## 🤝 Contribuição

Este é um projeto educacional. Para melhorias:

1. Ajuste os seletores CSS conforme mudanças no site
2. Adicione novos campos de extração conforme necessário
3. Otimize estratégias anti-detecção baseado no comportamento do site

## ⚖️ Considerações Legais

- Respeite sempre os termos de uso do site
- Use delays apropriados para não sobrecarregar o servidor
- Este código é para fins educacionais e de pesquisa
- Verifique a legalidade do web scraping em sua jurisdição

## 🆔 Versão

**Parts Unlimited Scraper v1.0.0**

Desenvolvido em Python com Playwright para máxima compatibilidade e robustez.