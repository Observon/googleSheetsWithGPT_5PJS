# Google Drive + GPT Data Analyzer

[![Tests](https://github.com/yourusername/googleSheetsWithGPT_5PJS/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/googleSheetsWithGPT_5PJS/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Ferramenta inteligente para análise automática de dados do Google Drive usando GPT**

Analisa planilhas do Google Drive, extrai insights em tempo real e gera relatórios em múltiplos formatos. Ideal para automação de análises repetitivas, processamento em lote e integração com pipelines de dados.

## 🎯 Características Principais

- **📋 Listagem de Planilhas** — Descubra todas as planilhas em sua conta ou pasta específica
- **🤖 Análise com GPT** — Use modelos GPT para análises profundas e automatizadas
- **💡 Insights Automáticos** — Gere relatórios com padrões, anomalias e recomendações
- **❓ Perguntas Customizadas** — Faça perguntas específicas sobre seus dados
- **💾 Exportação Flexível** — Exporte em CSV, PDF ou Markdown
- **📦 Processamento em Lote** — Processe múltiplas planilhas automaticamente
- **⏰ Agendamento** — Configure análises periódicas com cron expressions
- **⚡ Cache Inteligente** — Evite custos redundantes com análises em cache
- **🔗 API REST** — Use via FastAPI para integração programática
- **🔒 Segurança** — Credenciais seguras via service account + variáveis de ambiente

## ⚡ Quick Start (5 minutos)

### 1. Instalação

```bash
# Clone e acesse o repositório
git clone https://github.com/yourusername/googleSheetsWithGPT_5PJS.git
cd googleSheetsWithGPT_5PJS

# Crie um ambiente virtual
python -m venv .venv

# Ative (Windows)
.\.venv\Scripts\Activate.ps1

# ou (macOS/Linux)
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração

```bash
# Copie o template de variáveis
cp .env.example .env
```

Edite `.env` com suas credenciais:
```env
GOOGLE_CREDENTIALS_JSON=C:\caminho\para\credentials.json
OPENAI_API_KEY=sk-sua-chave-aqui
GOOGLE_DRIVE_FOLDER_ID=opcional
```

[Setup completo no SETUP.md](docs/SETUP.md)

### 3. Execute

```bash
# CLI Interativa
python gdrive_gpt_app.py

# ou diretamente
python -m src.cli.main
```

---

## 📚 Documentação

| Tópico | Link |
|--------|------|
| **Arquitetura & Design** | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Referência API REST** | [API.md](docs/API.md) |
| **Setup Avançado** | [SETUP.md](docs/SETUP.md) |
| **Como Contribuir** | [CONTRIBUTING.md](docs/CONTRIBUTING.md) |

---

## 🏗️ Arquitetura

Clean Architecture com separação clara de responsabilidades:

```
src/
├── domain/         # Modelos Pydantic + Custom Exceptions
├── adapters/       # Google Drive, OpenAI, Cache (integração externa)
├── services/       # Lógica de negócio (loader, analyzer, export, batch, scheduler)
├── cli/            # Interface CLI
└── api/            # FastAPI REST API
```

**Padrões:**
- ✅ **Dependency Injection** — Services recebem adapters no construtor
- ✅ **Clean Architecture** — Domain isolado de implementação
- ✅ **Repository Pattern** — Adapters encapsulam APIs externas
- ✅ **Exception Hierarchy** — Exceções customizadas para diferentes erros

---

## 🖥️ CLI (9 Opções)

```
1. 📋 Listar planilhas
2. 🔍 Analisar planilha (com prompt customizado)
3. 💡 Gerar insights automáticos
4. ❓ Fazer pergunta sobre dados carregados
5. 💾 Exportar análise (CSV/PDF/Markdown)
6. 📦 Processar lote de planilhas
7. ⏰ Agendar análises periódicas
8. 🗑️  Limpar cache
9. 🚪 Sair
```

---

## 🔌 API REST (FastAPI)

```bash
# Inicie o servidor
uvicorn src.api.main:app --reload

# Swagger UI interativo
http://localhost:8000/docs

# Exemplos:
curl http://localhost:8000/health
curl http://localhost:8000/sheets
```

📖 Documentação completa em [API.md](docs/API.md)

---

## 🧪 Testes

```bash
# Rodar testes
pytest tests/ -v

# Com cobertura (target: 50-70%)
pytest tests/ --cov=src --cov-report=html

# Tipos específicos
pytest tests/unit -v
pytest tests/integration -v
```

Todos testes possuem mocks para Google Drive e OpenAI (sem fazer calls reais).

---

## 🔒 Segurança

✅ Credenciais em variáveis de ambiente (nunca em código)  
✅ `.env` e `credentials.json` em `.gitignore`  
✅ Service Account com escopo **leitura-apenas**  
✅ Validação rigorosa com Pydantic  
✅ Sem dados sensíveis em logs

---

## 📦 Funcionalidades Detalhadas

### Exportação (CSV/PDF/Markdown)
- Múltiplos formatos para diferentes usos
- PDF profissional com ReportLab
- Markdown para documentação/blogs

### Cache
- **File-based** — Evita chamadas redundantes à OpenAI
- **Chave única** — Hash(spreadsheet_id + prompt)
- **Comando CLI** — Limpar cache conforme necessário

### Batch Processing
- Processe pastas inteiras automaticamente
- Progress bar com tqdm
- Exportação opcional em lote

### Agendamento (APScheduler)
- Cron expressions para frequência
- Persistência em `scheduled_jobs.json`
- Daemon mode para rodar em background

---

##  ✨ Exemplo de Uso Programático

```python
from src.services.analyzer import AnalyzerService
from src.adapters.google_drive import GoogleDriveAdapter

# Inicializar
drive = GoogleDriveAdapter()
analyzer = AnalyzerService()

# Listar planilhas
sheets = drive.list_spreadsheets()

# Analisar uma planilha
analysis = analyzer.analyze_spreadsheet(
    file_id=sheets[0].id,
    file_name=sheets[0].name,
    prompt="Quais são o padrões principais?"
)

print(analysis.result)
```

---

## 🐛 Troubleshooting

**GOOGLE_CREDENTIALS_JSON não encontrado**
```bash
1. Verifique se .env existe: cat .env
2. Coloque a credencial como JSON inline se preferir
3. Ou aponte para um arquivo: GOOGLE_CREDENTIALS_JSON=/caminho/ao/credentials.json
```

**Service Account não vê minhas planilhas**
```
→ Compartilhe a pasta com o email da Service Account
→ Email está em: client_email (arquivo JSON)
→ Permissão: Leitor (read-only)
```

**OpenAI returns rate limit error**
```
→ Aguarde alguns minutos
→ Considere usar cache (evita chamadas repetidas)
→ Aumente os limites na conta da OpenAI
```

---

## 📈 Performance

- **Cache Hit:** ~1000x mais rápido (arquivo local vs API)
- **Batch Processing:** ~10-20 planilhas/minuto (tamanho varia)
- **API Response:** ~200-500ms (Google Drive + OpenAI)

---

## 📋 Requirements

- Python 3.10+
- Google Cloud Project com Drive API ativada
- Service Account credentials (JSON)
- OpenAI API key

---

## 🚀 Desenvolvimento

```bash
# Code formatting
black src tests

# Linting
ruff check src tests

# Run everything
black src tests && ruff check src tests && pytest tests/
```

---

## 🛣️ Roadmap

- [ ] Suporte a banco de dados (SQLite/PostgreSQL)
- [ ] Async/await para melhor performance
- [ ] Docker & Docker Compose
- [ ] Webhook integration
- [ ] Dashboard web
- [ ] i18n (múltiplos idiomas)
- [ ] Visualizações em HTML/Charts

---

## 📄 Licença

MIT License © 2026 — Veja [LICENSE](LICENSE)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](docs/CONTRIBUTING.md) para detalhes.

```bash
1. Fork o projeto
2. Crie uma branch (git checkout -b feature/MyFeature)
3. Commit mudanças (git commit -m "Add MyFeature")
4. Push (git push origin feature/MyFeature)
5. Abra um Pull Request
```

---

## 💬 Suporte

- 🐛 [Report a Bug](https://github.com/yourusername/googleSheetsWithGPT_5PJS/issues)
- 💡 [Feature Request](https://github.com/yourusername/googleSheetsWithGPT_5PJS/issues)
- 📖 [Documentação](docs/)

---

## 👤 Autor

**Erick** — Full-Stack Developer

---

**Última atualização:** Março 2026
