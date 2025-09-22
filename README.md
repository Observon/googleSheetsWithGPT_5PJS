# Google Drive + GPT Data Analyzer

Aplicação de linha de comando que lista planilhas do Google Drive, carrega os dados em `pandas` e gera análises e insights com a API da OpenAI.

## Recursos

- Listagem de planilhas (`Google Sheets`) no seu Drive ou em uma pasta específica.
- Leitura da planilha como Excel via API do Drive e carregamento em `pandas`.
- Análise estruturada dos dados + geração de insights com modelos GPT.
- Interface simples em modo texto (menu interativo).

## Requisitos

- Python 3.9 ou superior (recomendado).
- Projeto no Google Cloud com a Google Drive API habilitada.
- Credenciais de conta de serviço (Service Account) com permissão de leitura na(s) pasta(s) desejada(s).
- Chave de API da OpenAI.

## Instalação

1. Crie e ative um ambiente virtual (recomendado):
   - PowerShell (Windows):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - CMD (Windows):
     ```bat
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Configuração

1. Habilite a Google Drive API e gere a conta de serviço:
   - Acesse o [Google Cloud Console](https://console.cloud.google.com/).
   - Crie um projeto (ou utilize um existente).
   - Habilite a Google Drive API.
   - Crie uma Service Account e faça o download do arquivo JSON de credenciais.
   - Compartilhe a(s) pasta(s) do Drive com o e-mail da Service Account (campo `client_email` do JSON), com permissão de Leitor.

2. Crie o arquivo `.env` (com base em `.env.example`):
   - Copie o exemplo:
     ```bash
     cp .env.example .env
     ```
   - Preencha as variáveis:
     - `GOOGLE_CREDENTIALS_JSON`: pode ser o caminho do arquivo JSON (ex.: `C:\\Users\\voce\\projeto\\credentials.json`) OU o conteúdo JSON completo inline (em uma única linha).
     - `OPENAI_API_KEY`: sua chave da OpenAI.
     - `GOOGLE_DRIVE_FOLDER_ID` (opcional): limite a listagem a uma pasta específica do Drive.

   Dica: para obter o `folder_id`, abra a pasta no Drive e copie a parte após `folders/` na URL.

3. Segurança de credenciais:
   - Nunca versione `credentials.json` ou `.env`.
   - Utilize apenas `GOOGLE_CREDENTIALS_JSON` apontando para um caminho local fora do repositório ou o JSON inline no `.env`.

## Execução

```bash
python gdrive_gpt_app.py
```

Você verá um menu com as opções:

1. Listar planilhas disponíveis
2. Analisar planilha específica (carrega os dados para memória)
3. Gerar insights automáticos (usa GPT sobre os dados carregados)
4. Fazer pergunta personalizada (prompt customizado para o GPT)
5. Sair

Fluxo sugerido:

1) Use a opção 2 para carregar uma planilha.
2) Então escolha a opção 3 (insights) ou 4 (pergunta personalizada).

## Notas importantes

- O carregamento da planilha é feito exportando como Excel pela API do Drive e lendo com `pandas` + `openpyxl`.
- Se sua planilha tem múltiplas abas, por padrão é carregada a primeira. Ajuste o código em `GoogleDriveProcessor.read_spreadsheet()` para informar `sheet_name` se desejar.
- O modelo padrão usado é `gpt-4o-mini` (configurável em `GPTDataAnalyzer.process_data_with_gpt()`).

## Solução de problemas

- Erro: `GOOGLE_CREDENTIALS_JSON not found` — Verifique se o `.env` foi criado e carregado corretamente, e se a variável está preenchida.
- A Service Account não vê suas planilhas — Compartilhe a pasta/arquivo com o e-mail da Service Account como Leitor.
- Erro ao ler Excel — Garanta que a dependência `openpyxl` está instalada (já presente no `requirements.txt`).
- Chave da OpenAI inválida — Verifique `OPENAI_API_KEY` e se sua conta possui créditos/limites.
- Permissões insuficientes — A aplicação utiliza escopo de leitura do Drive: `https://www.googleapis.com/auth/drive.readonly`.

## Segurança

- Não faça commit de `.env`, `credentials.json` ou chaves.
- Prefira armazenar `credentials.json` fora do repositório e referenciá-lo no `.env`.
- Revise periodicamente os acessos concedidos à Service Account.

### Se você comitou `credentials.json` por engano

1. Revogue/rote a chave no Google Cloud Console:
   - IAM & Admin > Service Accounts > [sua conta] > Keys > Delete a chave exposta e crie uma nova.
2. Remova o arquivo do histórico do Git e force push:
   - Usando `git filter-repo` (recomendado):
     ```bash
     pip install git-filter-repo
     git filter-repo --invert-paths --path credentials.json
     git push --force
     ```
   - Alternativa com `git filter-branch` (mais lento/legado):
     ```bash
     git filter-branch --force --index-filter "git rm --cached --ignore-unmatch credentials.json" --prune-empty --tag-name-filter cat -- --all
     git push --force --all
     git push --force --tags
     ```
3. Garanta que `.gitignore` contenha `credentials.json` (já incluído neste projeto).

## Estrutura principal do código

- `gdrive_gpt_app.py`
  - Classe `GoogleDriveProcessor`: autenticação com Service Account e leitura/listagem de planilhas.
  - Classe `GPTDataAnalyzer`: preparação do resumo dos dados e chamada à API da OpenAI.
  - Função `main()`: loop do menu e orquestração das ações.


### Como Obter as Credenciais

#### Google Drive API:

Acesse Google Cloud Console
Crie um projeto ou selecione um existente
Ative a Google Drive API
Crie uma conta de serviço
Baixe o arquivo JSON das credenciais

#### OpenAI API:

Acesse OpenAI Platform
Vá em "API Keys"
Crie uma nova chave