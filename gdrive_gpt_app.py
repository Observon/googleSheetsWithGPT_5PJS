import os
import io
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

class GoogleDriveProcessor:
    def __init__(self):
        # Initialize Google Drive API
        self.creds = None
        self.service = None
        self._initialize_google_drive()

    def _initialize_google_drive(self):
        """Initialize Google Drive API with service account credentials."""
        try:
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if not creds_json:
                raise ValueError("GOOGLE_CREDENTIALS_JSON not found in environment variables")
                
            creds_dict = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            self.service = build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"Error initializing Google Drive: {str(e)}")
            raise

    def list_spreadsheets(self, folder_id: str = None) -> List[Dict[str, str]]:
        """List all Google Sheets in the specified folder or root."""
        try:
            query = "mimeType='application/vnd.google-apps.spreadsheet'"
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            results = self.service.files().list(
                q=query,
                pageSize=10,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            print(f"Error listing spreadsheets: {str(e)}")
            return []

    def read_spreadsheet(self, file_id: str) -> pd.DataFrame:
        """Read a Google Sheet and return as pandas DataFrame."""
        try:
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
                print(f"Download {int(status.progress() * 100)}%")
            
            # Read the Excel file into a pandas DataFrame
            fh.seek(0)
            return pd.read_excel(fh, engine='openpyxl')
        except Exception as e:
            print(f"Error reading spreadsheet: {str(e)}")
            raise


class GPTChat:
    def __init__(self):
        """Initialize OpenAI API client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = openai.OpenAI(api_key=api_key)

    def process_data_with_gpt(self, data: pd.DataFrame, prompt: str) -> str:
        """Process data using GPT-4 with the given prompt."""
        try:
            # Convert DataFrame to string for the prompt
            data_str = data.head().to_string()  # Using head() to limit token usage
            
            # Create the full prompt
            full_prompt = f"""You are a data analysis assistant. Here's some data:
            
            {data_str}
            
            {prompt}
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes spreadsheet data."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error processing data with GPT: {str(e)}")
            raise


def main():
    try:
        # Initialize classes
        drive_processor = GoogleDriveProcessor()
        gpt_chat = GPTChat()
        
        # List available spreadsheets
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        spreadsheets = drive_processor.list_spreadsheets(folder_id)
        
        if not spreadsheets:
            print("No spreadsheets found!")
            return
            
        print("\nAvailable spreadsheets:")
        for i, sheet in enumerate(spreadsheets, 1):
            print(f"{i}. {sheet['name']} (ID: {sheet['id']})")
        
        # Let user select a spreadsheet
        while True:
            try:
                choice = int(input("\nEnter the number of the spreadsheet to analyze: ")) - 1
                if 0 <= choice < len(spreadsheets):
                    selected = spreadsheets[choice]
                    break
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Read the selected spreadsheet
        print(f"\nReading spreadsheet: {selected['name']}...")
        df = drive_processor.read_spreadsheet(selected['id'])
        
        # Show a preview of the data
        print("\nPreview of the data:")
        print(df.head())
        
        # Get user prompt
        print("\nEnter your analysis prompt (e.g., 'What are the key insights from this data?'):")
        user_prompt = input("> ")
        
        # Process with GPT
        print("\nAnalyzing data with GPT-4...")
        result = gpt_chat.process_data_with_gpt(df, user_prompt)
        
        # Display results
        print("\nAnalysis Results:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
