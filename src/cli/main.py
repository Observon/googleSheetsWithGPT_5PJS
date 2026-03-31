"""Command-line interface for Google Drive + GPT Data Analyzer."""

import logging
import os
import sys
from pathlib import Path

from src.config import settings
from src.services.data_loader import DataLoaderService
from src.services.analyzer import AnalyzerService
from src.services.export import ExportService
from src.services.batch import BatchService
from src.services.scheduler import SchedulerService
from src.domain.exceptions import ApplicationError

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CLIApplication:
    """Main CLI application."""

    def __init__(self):
        """Initialize CLI application with services."""
        try:
            self.data_loader = DataLoaderService()
            self.analyzer = AnalyzerService()
            self.export_service = ExportService()
            self.batch_service = BatchService()
            self.scheduler = SchedulerService()

            self.current_dataset = None
            self.current_file_name = ""
            self.current_file_id = ""

        except ApplicationError as e:
            logger.error(f"Failed to initialize application: {e}")
            sys.exit(1)

    def display_menu(self):
        """Display the main menu."""
        print("\n" + "=" * 70)
        print("📊 GOOGLE DRIVE + GPT DATA ANALYZER v1.0")
        print("=" * 70)
        print("1. 📋 Listar planilhas disponíveis")
        print("2. 🔍 Analisar planilha específica")
        print("3. 💡 Gerar insights automáticos")
        print("4. ❓ Fazer pergunta personalizada")
        print("5. 💾 Exportar última análise (CSV/PDF/MD)")
        print("6. 📦 Processar lote de planilhas")
        print("7. ⏰ Agendar análises periódicas")
        print("8. 🗑️  Limpar cache")
        print("9. 🚪 Sair")
        print("=" * 70)

    def list_spreadsheets(self):
        """List available spreadsheets."""
        print("\n🔍 Buscando planilhas...")
        try:
            folder_id = settings.google_drive_folder_id
            spreadsheets = self.data_loader.list_spreadsheets(folder_id)

            if not spreadsheets:
                print("❌ Nenhuma planilha encontrada!")
                return

            print(f"\n📁 Planilhas encontradas ({len(spreadsheets)}):")
            print("-" * 80)
            for i, sheet in enumerate(spreadsheets, 1):
                modified = (
                    sheet.modified_time[:10] if sheet.modified_time else "N/A"
                )
                print(f"{i:2d}. 📊 {sheet.name}")
                print(f"     ID: {sheet.id} | Modificado: {modified}")
                print()

        except ApplicationError as e:
            print(f"❌ Erro ao listar planilhas: {e}")

    def analyze_spreadsheet(self):
        """Analyze a specific spreadsheet."""
        try:
            folder_id = settings.google_drive_folder_id
            spreadsheets = self.data_loader.list_spreadsheets(folder_id)

            if not spreadsheets:
                print("❌ Nenhuma planilha encontrada!")
                return

            print(f"\nEscolha uma planilha (1-{len(spreadsheets)}):")
            for i, sheet in enumerate(spreadsheets, 1):
                print(f"{i}. {sheet.name}")

            try:
                sheet_choice = int(input("\nNúmero da planilha: ")) - 1
                if 0 <= sheet_choice < len(spreadsheets):
                    selected = spreadsheets[sheet_choice]

                    # Prompt from user
                    print("\nDigite sua pergunta ou deixe em branco para análise padrão:")
                    prompt = input("> ").strip()

                    if not prompt:
                        print("\n💡 Gerando insights automáticos...")
                        analysis = self.analyzer.generate_insights(
                            selected.id, selected.name
                        )
                    else:
                        print("\n🔍 Analisando com sua pergunta...")
                        analysis = self.analyzer.analyze_spreadsheet(
                            selected.id, selected.name, prompt
                        )

                    # Store for later export
                    self.current_file_id = selected.id
                    self.current_file_name = selected.name

                    # Display result
                    print("\n" + "=" * 70)
                    print(f"📊 Análise: {selected.name}")
                    print("=" * 70)
                    if analysis.cached:
                        print("💾 [RESULTADO EM CACHE]")
                    print(analysis.result)
                    print("=" * 70)

                else:
                    print("❌ Seleção inválida!")

            except ValueError:
                print("❌ Por favor, insira um número válido!")

        except ApplicationError as e:
            print(f"❌ Erro ao analisar: {e}")

    def generate_insights(self):
        """Generate automatic insights."""
        try:
            folder_id = settings.google_drive_folder_id
            spreadsheets = self.data_loader.list_spreadsheets(folder_id)

            if not spreadsheets:
                print("❌ Nenhuma planilha encontrada!")
                return

            print(f"\nEscolha uma planilha (1-{len(spreadsheets)}):")
            for i, sheet in enumerate(spreadsheets, 1):
                print(f"{i}. {sheet.name}")

            try:
                sheet_choice = int(input("\nNúmero da planilha: ")) - 1
                if 0 <= sheet_choice < len(spreadsheets):
                    selected = spreadsheets[sheet_choice]
                    print(f"\n💡 Gerando insights para: {selected.name}...")

                    analysis = self.analyzer.generate_insights(
                        selected.id, selected.name
                    )

                    self.current_file_id = selected.id
                    self.current_file_name = selected.name

                    print("\n" + "=" * 70)
                    print(f"📊 Insights: {selected.name}")
                    print("=" * 70)
                    print(analysis.result)
                    print("=" * 70)

                else:
                    print("❌ Seleção inválida!")

            except ValueError:
                print("❌ Por favor, insira um número válido!")

        except ApplicationError as e:
            print(f"❌ Erro ao gerar insights: {e}")

    def custom_question(self):
        """Ask a custom question about the data."""
        if not self.current_file_id:
            print("❌ Nenhuma planilha carregada! Execute a opção 2 primeiro.")
            return

        try:
            print(f"\nPlanilha atual: {self.current_file_name}")
            prompt = input("Digite sua pergunta: ").strip()

            if not prompt:
                print("❌ Pergunta vazia!")
                return

            print("\n🔍 Processando sua pergunta...")

            analysis = self.analyzer.analyze_spreadsheet(
                self.current_file_id, self.current_file_name, prompt
            )

            print("\n" + "=" * 70)
            print("🔍 Resposta")
            print("=" * 70)
            print(analysis.result)
            print("=" * 70)

        except ApplicationError as e:
            print(f"❌ Erro ao processar pergunta: {e}")

    def export_analysis(self):
        """Export the last analysis."""
        if not self.current_file_id:
            print("❌ Nenhuma análise para exportar! Execute a opção 2 primeiro.")
            return

        try:
            print("\nFormatos disponíveis:")
            print("1. CSV")
            print("2. PDF")
            print("3. Markdown")

            try:
                choice = int(input("\nEscolha um formato (1-3): "))
                formats = {1: "csv", 2: "pdf", 3: "md"}

                if choice not in formats:
                    print("❌ Opção inválida!")
                    return

                format_choice = formats[choice]

                # Generate a simple analysis if needed
                print(f"\n💾 Exportando em {format_choice.upper()}...")
                analysis = self.analyzer.generate_insights(
                    self.current_file_id, self.current_file_name
                )

                export_result = self.export_service.export_analysis(
                    analysis, format_choice
                )

                print(
                    f"✅ Exportado com sucesso: {export_result.filepath} ({export_result.size_bytes} bytes)"
                )

            except ValueError:
                print("❌ Por favor, insira um número válido!")

        except ApplicationError as e:
            print(f"❌ Erro ao exportar: {e}")

    def batch_process(self):
        """Process a batch of spreadsheets."""
        try:
            folder_id = input("Digite o ID da pasta do Google Drive: ").strip()
            if not folder_id:
                print("❌ ID da pasta obrigatório!")
                return

            prompt = input(
                "Digite um texto para análise ou deixe em branco para insights padrão: "
            ).strip()

            if not prompt:
                prompt = """
Analise estes dados e forneça:
1. Principais insights e padrões identificados
2. Anomalias ou valores interessantes
3. Recomendações de ações baseadas nos dados
"""

            export_format = input(
                "Digite um formato de exportação (csv/pdf/md) ou deixe em branco para não exportar: "
            ).strip()
            if not export_format:
                export_format = None

            print(f"\n📦 Iniciando processamento em lote...")
            results = self.batch_service.process_folder(
                folder_id, prompt, export_format
            )

            print("\n" + "=" * 70)
            print("📊 Resultados do Processamento em Lote")
            print("=" * 70)
            successful = sum(1 for r in results if r.get("status") == "success")
            failed = sum(1 for r in results if r.get("status") == "error")

            print(f"✅ Sucesso: {successful}")
            print(f"❌ Erros: {failed}")

            for result in results:
                status_icon = "✅" if result.get("status") == "success" else "❌"
                print(f"\n{status_icon} {result.get('file_name', 'Unknown')}")
                if result.get("export_path"):
                    print(f"   Exportado: {result['export_path']}")
                if result.get("error"):
                    print(f"   Erro: {result['error']}")

        except ApplicationError as e:
            print(f"❌ Erro no processamento em lote: {e}")

    def schedule_analysis(self):
        """Schedule periodic analysis."""
        try:
            job_id = input("Digite um ID para o trabalho (ex: daily_analysis): ").strip()
            folder_id = input("Digite o ID da pasta do Google Drive: ").strip()
            cron = input(
                "Digite a expressão cron (ex: '0 9 * * MON' para 9h toda segunda): "
            ).strip()
            prompt = input("Digite o prompt de análise ou deixe em branco para insights: ").strip()

            if not all([job_id, folder_id, cron]):
                print("❌ Todos os campos são obrigatórios!")
                return

            if not prompt:
                prompt = "Forneça insights principais dos dados"

            job_config = self.scheduler.schedule_analysis(
                job_id, folder_id, prompt, cron
            )

            print(f"\n✅ Trabalho agendado com sucesso!")
            print(f"ID: {job_config['job_id']}")
            print(f"Expressão cron: {job_config['cron']}")

            # Optionally start scheduler
            start = input("\nDeseja iniciar o agendador agora? (s/n): ").strip().lower()
            if start == "s":
                self.scheduler.start()
                print("✅ Agendador iniciado!")

        except ApplicationError as e:
            print(f"❌ Erro ao agendar: {e}")

    def clear_cache(self):
        """Clear the analysis cache."""
        try:
            confirm = (
                input("Tem certeza que deseja limpar todo o cache? (s/n): ")
                .strip()
                .lower()
            )
            if confirm == "s":
                count = self.analyzer.clear_cache()
                print(f"✅ Cache limpo! {count} entradas deletadas.")
            else:
                print("Operação cancelada.")
        except ApplicationError as e:
            print(f"❌ Erro ao limpar cache: {e}")

    def run(self):
        """Run the main application loop."""
        print("\n✅ Aplicação iniciada com sucesso!")

        while True:
            self.display_menu()

            try:
                choice = input("\nEscolha uma opção (1-9): ").strip()

                if choice == "1":
                    self.list_spreadsheets()

                elif choice == "2":
                    self.analyze_spreadsheet()

                elif choice == "3":
                    self.generate_insights()

                elif choice == "4":
                    self.custom_question()

                elif choice == "5":
                    self.export_analysis()

                elif choice == "6":
                    self.batch_process()

                elif choice == "7":
                    self.schedule_analysis()

                elif choice == "8":
                    self.clear_cache()

                elif choice == "9":
                    print("\n👋 Até logo!")
                    break

                else:
                    print("❌ Opção inválida!")

            except KeyboardInterrupt:
                print("\n\n👋 Aplicação interrompida pelo usuário")
                break

            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                logger.exception("Unexpected error in CLI")


def main():
    """Entry point for the CLI application."""
    try:
        app = CLIApplication()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
