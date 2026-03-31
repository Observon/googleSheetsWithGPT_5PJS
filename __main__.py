"""
Compatibility entry point for the CLI application.

Standard Python entry point for module execution: python -m googlesheets-gpt-analyzer
while delegating to the refactored src.cli.main module.
"""

if __name__ == "__main__":
    from src.cli.main import main
    main()
