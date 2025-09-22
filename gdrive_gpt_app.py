import os
import io
import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class GoogleDriveProcessor:
    def __init__(self):
        """Initialize Google Drive API client."""
        self.creds = None
        self.service = None
        self._initialize_google_drive()

    def _initialize_google_drive(self):
        """Initialize Google Drive API with service account credentials."""
        try:
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if not creds_json:
                raise ValueError("GOOGLE_CREDENTIALS_JSON not found in environment variables")
                
            # Handle both file path and JSON string
            if creds_json.startswith('{'):
                # Direct JSON string
                creds_dict = json.loads(creds_json)
            else:
                # File path
                with open(creds_json, 'r') as f:
                    creds_dict = json.load(f)
            
            self.creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("Google Drive API initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Google Drive: {str(e)}")
            raise

    def list_spreadsheets(self, folder_id: Optional[str] = None) -> List[Dict[str, str]]:
        """List all Google Sheets in the specified folder or root."""
        try:
            query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            results = self.service.files().list(
                q=query,
                pageSize=50,  # Increased limit
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                orderBy="modifiedTime desc"  # Most recent first
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} spreadsheets")
            return files
            
        except Exception as e:
            logger.error(f"Error listing spreadsheets: {str(e)}")
            return []

    def read_spreadsheet(self, file_id: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Read a Google Sheet and return as pandas DataFrame."""
        try:
            logger.info(f"Reading spreadsheet with ID: {file_id}")
            
            # Export the Google Sheet as Excel
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Download the file
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")
            
            # Read the Excel file into a pandas DataFrame
            fh.seek(0)
            df = pd.read_excel(fh, engine='openpyxl', sheet_name=sheet_name)
            
            if isinstance(df, dict):
                # Multiple sheets - return the first one or specified sheet
                df = df[list(df.keys())[0]] if not sheet_name else df[sheet_name]
            
            logger.info(f"Successfully loaded spreadsheet with shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error reading spreadsheet: {str(e)}")
            raise

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get detailed information about a file."""
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, owners"
            ).execute()
            return file_info
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {}


class GPTDataAnalyzer:
    def __init__(self):
        """Initialize OpenAI API client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")

    def analyze_data_structure(self, df: pd.DataFrame) -> str:
        """Analyze the structure of the DataFrame."""
        info = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "sample_data": df.head(3).to_dict()
        }
        return json.dumps(info, indent=2, default=str)

    def prepare_data_summary(self, df: pd.DataFrame, max_rows: int = 20) -> str:
        """Prepare a concise data summary for GPT processing."""
        # Basic info
        summary = f"Dataset Info:\n"
        summary += f"- Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
        summary += f"- Columns: {', '.join(df.columns.astype(str))}\n\n"
        
        # Data types
        summary += "Data Types:\n"
        for col, dtype in df.dtypes.items():
            summary += f"- {col}: {dtype}\n"
        
        # Sample data
        summary += f"\nSample Data (first {min(max_rows, len(df))} rows):\n"
        summary += df.head(max_rows).to_string(index=False, max_cols=10)
        
        # Basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary += "\n\nNumeric Statistics:\n"
            summary += df[numeric_cols].describe().to_string()
        
        return summary

    def process_data_with_gpt(self, df: pd.DataFrame, prompt: str, model: str = "gpt-4o-mini") -> str:
        """Process data using GPT with the given prompt."""
        try:
            # Prepare data summary
            data_summary = self.prepare_data_summary(df)
            
            # Create the full prompt
            full_prompt = f"""
Você é um especialista em análise de dados. Analise os seguintes dados e responda à pergunta do usuário.

DADOS:
{data_summary}

PERGUNTA DO USUÁRIO:
{prompt}

Por favor, forneça uma análise detalhada, insights relevantes e recomendações baseadas nos dados apresentados.
Se necessário, sugira visualizações ou análises adicionais que poderiam ser úteis.
"""
            
            logger.info(f"Sending request to {model}")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um assistente especializado em análise de dados e insights de negócio. Forneça respostas claras, objetivas e acionáveis."
                    },
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error processing data with GPT: {str(e)}")
            raise

    def generate_insights(self, df: pd.DataFrame) -> str:
        """Generate automatic insights from the data."""
        prompt = """
Analise estes dados e forneça:
1. Principais insights e padrões identificados
2. Anomalias ou valores interessantes
3. Correlações importantes (se aplicável)
4. Recomendações de ações baseadas nos dados
5. Sugestões de análises adicionais que poderiam ser valiosas
"""
        return self.process_data_with_gpt(df, prompt)


def display_menu():
    """Display the main menu options."""
    print("\n" + "="*60)
    print("📊 GOOGLE DRIVE + GPT DATA ANALYZER")
    print("="*60)
    print("1. 📋 Listar planilhas disponíveis")
    print("2. 🔍 Analisar planilha específica")
    print("3. 💡 Gerar insights automáticos")
    print("4. ❓ Fazer pergunta personalizada")
    print("5. 🚪 Sair")
    print("="*60)


def main():
    try:
        # Initialize classes
        drive_processor = GoogleDriveProcessor()
        gpt_analyzer = GPTDataAnalyzer()
        
        current_df = None
        current_file_name = ""
        
        while True:
            display_menu()
            
            try:
                choice = input("\nEscolha uma opção (1-5): ").strip()
                
                if choice == "1":
                    # List spreadsheets
                    print("\n🔍 Buscando planilhas...")
                    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
                    spreadsheets = drive_processor.list_spreadsheets(folder_id)
                    
                    if not spreadsheets:
                        print("❌ Nenhuma planilha encontrada!")
                        continue
                        
                    print(f"\n📁 Planilhas encontradas ({len(spreadsheets)}):")
                    print("-" * 80)
                    for i, sheet in enumerate(spreadsheets, 1):
                        modified = sheet.get('modifiedTime', 'N/A')[:10] if sheet.get('modifiedTime') else 'N/A'
                        print(f"{i:2d}. 📊 {sheet['name']}")
                        print(f"     ID: {sheet['id']} | Modificado: {modified}")
                        print()
                
                elif choice == "2":
                    # Analyze specific spreadsheet
                    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
                    spreadsheets = drive_processor.list_spreadsheets(folder_id)
                    
                    if not spreadsheets:
                        print("❌ Nenhuma planilha encontrada!")
                        continue
                    
                    print(f"\nEscolha uma planilha (1-{len(spreadsheets)}):")
                    for i, sheet in enumerate(spreadsheets, 1):
                        print(f"{i}. {sheet['name']}")
                    
                    try:
                        sheet_choice = int(input("\nNúmero da planilha: ")) - 1
                        if 0 <= sheet_choice < len(spreadsheets):
                            selected = spreadsheets[sheet_choice]
                            print(f"\n📖 Carregando: {selected['name']}...")
                            
                            current_df = drive_processor.read_spreadsheet(selected['id'])
                            current_file_name = selected['name']
                            
                            print("\n✅ Planilha carregada com sucesso!")
                            print(f"📊 Dimensões: {current_df.shape[0]} linhas, {current_df.shape[1]} colunas")
                            print("\n🔍 Preview dos dados:")
                            print(current_df.head().to_string(max_cols=10))
                        else:
                            print("❌ Seleção inválida!")
                    except ValueError:
                        print("❌ Por favor, insira um número válido!")
                
                elif choice == "3":
                    # Generate automatic insights
                    if current_df is None:
                        print("❌ Primeiro carregue uma planilha (opção 2)!")
                        continue
                    
                    print(f"\n🧠 Gerando insights automáticos para: {current_file_name}")
                    print("⏳ Aguarde, analisando com GPT...")
                    
                    insights = gpt_analyzer.generate_insights(current_df)
                    
                    print("\n" + "="*60)
                    print("💡 INSIGHTS AUTOMÁTICOS")
                    print("="*60)
                    print(insights)
                    print("="*60)
                
                elif choice == "4":
                    # Custom question
                    if current_df is None:
                        print("❌ Primeiro carregue uma planilha (opção 2)!")
                        continue
                    
                    print(f"\n💬 Fazendo pergunta sobre: {current_file_name}")
                    user_prompt = input("🤔 Sua pergunta: ").strip()
                    
                    if not user_prompt:
                        print("❌ Pergunta não pode estar vazia!")
                        continue
                    
                    print("⏳ Processando com GPT...")
                    result = gpt_analyzer.process_data_with_gpt(current_df, user_prompt)
                    
                    print("\n" + "="*60)
                    print("🤖 RESPOSTA DO GPT")
                    print("="*60)
                    print(result)
                    print("="*60)
                
                elif choice == "5":
                    print("\n👋 Obrigado por usar o Google Drive + GPT Analyzer!")
                    break
                
                else:
                    print("❌ Opção inválida! Escolha entre 1-5.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Programa interrompido pelo usuário.")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                print(f"❌ Erro inesperado: {str(e)}")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"❌ Erro fatal: {str(e)}")
        print("🔧 Verifique sua configuração e tente novamente.")


if __name__ == "__main__":
    main()