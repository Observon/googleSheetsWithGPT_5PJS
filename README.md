# Google Drive to GPT Integration

This application allows you to access Google Drive, read spreadsheets, and analyze the data using OpenAI's GPT-4 model.

## Features

- List and access Google Sheets from your Google Drive
- Read spreadsheet data into pandas DataFrames
- Process and analyze data using GPT-4
- Simple command-line interface

## Prerequisites

1. Python 3.8 or higher
2. Google Cloud Project with Google Drive API enabled
3. Service account credentials for Google Drive API
4. OpenAI API key

## Setup Instructions

1. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Drive API**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Create a service account
   - Download the service account credentials as JSON
   - Share your Google Drive folder with the service account email (you can find it in the credentials JSON file)

3. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Paste your service account credentials JSON content into `GOOGLE_CREDENTIALS_JSON`
   - Add your OpenAI API key to `OPENAI_API_KEY`
   - (Optional) Add a Google Drive folder ID to `GOOGLE_DRIVE_FOLDER_ID`

## Usage

1. Run the application:
   ```bash
   python gdrive_gpt_app.py
   ```

2. Follow the on-screen prompts to:
   - Select a spreadsheet from your Google Drive
   - Enter a prompt for GPT to analyze the data
   - View the analysis results

## Example Prompts

- "What are the key trends in this data?"
- "Summarize the main points from this spreadsheet."
- "Are there any outliers or anomalies in this data?"
- "Provide a detailed analysis of the sales data."

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys and credentials secure
- The application only requests read access to your Google Drive
- Review the permissions granted to the service account

## Troubleshooting

- If you get authentication errors, verify your service account credentials
- Ensure the service account has access to the Google Drive folder
- Check that your OpenAI API key is valid and has sufficient credits
