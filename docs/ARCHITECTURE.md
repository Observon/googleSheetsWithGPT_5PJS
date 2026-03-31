# Architecture & Design

## Overview

Este projeto segue **Clean Architecture** com separação clara entre camadas de domínio, aplicação e infraestrutura.

```
┌─────────────────────────────────────────────────────┐
│                     CLI/FastAPI                      │ (Presentation Layer)
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                     Services                         │ (Application Layer)
│  (DataLoader, Analyzer, Export, Batch, Scheduler)   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                     Adapters                         │ (Infrastructure Layer)
│  (GoogleDrive, OpenAI, Cache)                        │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                   External APIs                      │ (Outside World)
│  (Google Drive, OpenAI)                              │
└─────────────────────────────────────────────────────┘
```

---

## Componentes Principais

### 1. Domain Layer (`src/domain/`)

**Responsabilidade:** Definir entidades e regras de negócio

**Arquivos:**
- `models.py` — **Pydantic models** para validação
  - `FileInfo` — Metadados de arquivo Google Drive
  - `Dataset` — Dados carregados do Drive
  - `Analysis` — Resultado de análise
  - `ExportResult` — Resultado de exportação

- `exceptions.py` — **Custom exceptions**
  - `GoogleDriveError` — Erros da API Google Drive
  - `OpenAIError` — Erros da API OpenAI
  - `ConfigError` — Erros de configuração
  - `ValidationError` — Erros de validação

**Benefício:** Domain isolado de detalhes de implementação. Fácil testar e entender lógica pura de negócio.

---

### 2. Adapters Layer (`src/adapters/`)

**Responsabilidade:** Encapsular integrações com APIs externas

**Arquivos:**
- `google_drive.py` — **GoogleDriveAdapter**
  - Inicializa service account
  - Lista planilhas
  - Lê spreadsheets via API Export → Excel → Pandas
  - Obtém metadados de arquivos
  - **Não valida dados**, apenas faz chamadas

- `openai_client.py` — **OpenAIAdapter**
  - Inicializa cliente OpenAI
  - Prepara resumo de dados
  - Envia prompts para GPT
  - Retorna análises brutas
  - **Não faz cache ou lógica de negócio**

- `cache.py` — **CacheAdapter**
  - File-based storage em `.cache/`
  - Keys = hash(spreadsheet_id + prompt)
  - CRUD: get, set, exists, delete, clear
  - **Transparente para serviços**

**Padrão:** Dependency Injection
```python
class AnalyzerService:
    def __init__(self, openai_adapter: Optional[OpenAIAdapter] = None):
        self.openai = openai_adapter or OpenAIAdapter()
```

**Benefício:** Fácil mockar em testes. APIs externas isoladas. Swap alternativas sem quebrar fluxo.

---

### 3. Services Layer (`src/services/`)

**Responsabilidade:** Lógica de negócio que orquestra adapters

**Arquivos:**

- `data_loader.py` — **DataLoaderService**
  ```
  Fluxo:
  1. Recebe GoogleDriveAdapter (injeção)
  2. Chama drive_adapter.read_spreadsheet()
  3. Valida DataFrame (empty check, columns check)
  4. Retorna Dataset object (domain model)
  ```

- `analyzer.py` — **AnalyzerService**
  ```
  Fluxo:
  1. Check cache com CacheAdapter (evita chamadas)
  2. If miss: Chama openai_adapter.process_data_with_gpt()
  3. Salva resultado no cache
  4. Retorna Analysis object
  Responsabilidades: Orquestração + Cache
  ```

- `export.py` — **ExportService**
  ```
  Fluxo:
  1. Recebe Analysis object
  2. Valida formato (csv/pdf/md)
  3. Exporta com ReportLab (PDF) ou nativo (CSV/MD)
  4. Retorna ExportResult com filepath + size
  ```

- `batch.py` — **BatchService**
  ```
  Fluxo:
  1. Lista planilhas em folder (drive_adapter)
  2. Loop: analyzer.analyze_spreadsheet() para cada
  3. Progress tracking com tqdm
  4. Coleta resultados (sucesso/erro)
  5. Retorna lista de results
  ```

- `scheduler.py` — **SchedulerService**
  ```
  Fluxo:
  1. APScheduler para cron jobs
  2. Schedule analysis com folder_id + prompt + cron
  3. Persistência em scheduled_jobs.json
  4. start() / stop() para daemon
  ```

**Pattern:** Services são **stateless** e **injectable**

**Benefício:** Lógica pura e testável. Fácil compor serviços. Adapters trocáveis sem mudanças.

---

### 4. Config Layer (`src/config.py`)

**Responsabilidade:** Leitura e validação de variáveis de ambiente

**Features:**
- Pydantic Settings para validação automática
- Leitura de `.env` file
- Suporte para JSON credentials (file ou inline)
- Lazy initialization de diretórios

```python
settings.get_credentials_dict()  # Parse JSON (file ou string)
settings.ensure_directories()   # Create cache + output dirs
```

**Benefício:** Type-safe configuration. Validation automática. Default values.

---

### 5. CLI Layer (`src/cli/main.py`)

**Responsabilidade:** Interface de usuário interativa

**Features:**
- 9 opções de menu
- Orquestra services
- User-friendly prompts + feedback
- Error handling gracioso
- Progress tracking

**Fluxo:**
```
Display Menu
  → User escolhe opção (1-9)
    → CLIApplication chama services
      → Services orquestram adapters
        → Adapters falam com APIs externas
      → Resultados retornam
    → Exibe resultado formatado
  → Volta para menu
```

---

### 6. API Layer (`src/api/main.py`)

**Responsabilidade:** REST API via FastAPI

**Features:**
- Health check: `GET /health`
- Listar sheets: `GET /sheets`
- Analisar: `POST /sheets/{id}/analyze`
- Exports: `GET /exports/{id}/{format}`
- Swagger UI automático em `/docs`

**Fluxo:**
```
HTTP POST /sheets/{id}/analyze
  ├─ Recebe JSON: {"prompt": "..."}
  ├─ Cria AnalyzerService()
  ├─ analyzer.analyze_spreadsheet(...)
  └─ Retorna JSON com resultado
```

---

## Data Flow Examples

### 1. User Analyzes Spreadsheet (CLI)

```
User digita "2" no menu
  ↓
CLIApplication.analyze_spreadsheet()
  ├─ drive.list_spreadsheets()           [GoogleDriveAdapter]
  ├─ User escolhe planilha
  ├─ User digita pergunta
  ├─ analyzer.analyze_spreadsheet()      [AnalyzerService]
  │   ├─ cache.get(sheet_id, prompt)     [CacheAdapter]
  │   ├─ if miss: drive.read_spreadsheet() [GoogleDriveAdapter]
  │   ├─ openai.process_data_with_gpt()  [OpenAIAdapter]
  │   └─ cache.set(...)
  └─ Exibe resultado
```

### 2. Batch Process Folder

```
User digita "6" no menu
  ↓
CLIApplication.batch_process()
  ├─ batch_service.process_folder(folder_id)        [BatchService]
  │   ├─ drive.list_spreadsheets(folder_id)         [GoogleDriveAdapter]
  │   ├─ for each sheet: analyzer.analyze_spreadsheet()
  │   ├─ if format: export_service.export_analysis()
  │   └─ collect results[]
  └─ Exibe summary
```

### 3. API Request

```
POST /sheets/{sheet_id}/analyze
  ↓
api/routes/analysis.py
  ├─ analyzer_service.analyze_spreadsheet()   [AnalyzerService]
  │   ├─ cache.get()                         [CacheAdapter]
  │   ├─ drive.read_spreadsheet()            [GoogleDriveAdapter]
  │   └─ openai.process_data_with_gpt()      [OpenAIAdapter]
  └─ Return JSON response
```

---

## Design Patterns Used

### 1. Dependency Injection
```python
class AnalyzerService:
    def __init__(self, openai_adapter: Optional[OpenAIAdapter] = None):
        self.openai = openai_adapter or OpenAIAdapter()
```
**Benefit:** Fácil mockar em testes. Flexível.

### 2. Repository Pattern (Adapters)
Adapters encapsulam acesso a APIs externas:
```python
class GoogleDriveAdapter:  # Repository
    def list_spreadsheets(...) -> List[FileInfo]
    def read_spreadsheet(...) -> pd.DataFrame
```

### 3. Service Locator (Config)
```python
from src.config import settings
settings.google_credentials_json
settings.openai_api_key
```

### 4. Exception Hierarchy
```
ApplicationError
  ├─ GoogleDriveError
  ├─ OpenAIError
  ├─ ConfigError
  └─ ValidationError
```

### 5. Factory Pattern (Services)
CLI instancia services conforme necessário:
```python
self.analyzer = AnalyzerService()  # Cria com defaults
self.export_service = ExportService()
```

---

## Error Handling

**Strategy:** Exceptions propagam para camadas superiores

```
Adapter raises GoogleDriveError
  ↓
Service catches, logs, re-raises with context
  ↓
CLI catches, exibe mensagem amigável
  ↓
User vê ❌ erro legível
```

**Benefit:** Proper logging. User-friendly messages. Debugging facilitado.

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Mock Google Drive + OpenAI
- Testam services em isolamento
- Use fixtures do conftest.py

```python
def test_analyzer_with_cache(analyzer_service, mock_cache):
    # Arrange
    analyzer_service.cache = mock_cache
    
    # Act
    result = analyzer_service.analyze_spreadsheet(...)
    
    # Assert
    mock_cache.get.assert_called_once()
```

### Integration Tests (`tests/integration/`)
- Fluxo end-to-end com mocks
- Validar orquestração entre serviços

### Coverage Target
- **50-70%** — Foco em services e domain
- Menos em CLI (UI) e adapters (externos)

---

## Scalability Notes

**Current:**
- Single-threaded, synchronous
- File-based cache (local)
- No database

**For Production:**
- [ ] Add async/await (Python 3.10+)
- [ ] PostgreSQL para cache + histórico
- [ ] Queue system (Celery) para batch jobs
- [ ] Webhook para notificações
- [ ] API rate limiting + auth
- [ ] Docker Compose para local dev

---

## Configuration Management

**Environment Variables:**
```env
GOOGLE_CREDENTIALS_JSON      # Required
OPENAI_API_KEY              # Required
GOOGLE_DRIVE_FOLDER_ID      # Optional
LOG_LEVEL                   # Default: INFO
CACHE_DIR                   # Default: .cache
OUTPUT_DIR                  # Default: output
MAX_SPREADSHEET_SIZE_MB     # Default: 100
```

**Validation:** Pydantic Settings valida em startup

---

## Module Dependencies

```
        CLI/API
         ↙  ↖
    Services
     ↙ ↓ ↖
Adapters
    ↓
External APIs
```

**Import rule:** Lower layers never import from upper layers

---

## Future Improvements

1. **Async Support**
   - Use FastAPI async routes
   - Concurrent batch processing

2. **Database**
   - SQLite for development
   - PostgreSQL for production
   - Store analysis history

3. **Authentication**
   - API keys for REST endpoints
   - Role-based access control

4. **Monitoring**
   - Prometheus metrics
   - ELK stack for logging
   - Sentry for error tracking

5. **Performance**
   - Query caching (Redis)
   - Request batching
   - Connection pooling

---

**Last Updated:** March 2026
