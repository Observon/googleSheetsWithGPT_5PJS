"Compatibility entry point for the CLI application.

This file maintains backward compatibility with the original gdrive_gpt_app.py
while delegating to the refactored src.cli.main module.
"

if __name__ == "__main__":
    from src.cli.main import main
    main()
