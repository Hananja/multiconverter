# src/multiconverter/gui/__main__.py
"""
Entry Point für die multiconverter GUI - startet die Hauptapplikation
"""
import flet as ft
from .main_app import MultiConverterApp

def main():
    """Hauptfunktion für den GUI-Start"""
    def app_main(page: ft.Page):
        app = MultiConverterApp(page)
        app.run()

    ft.app(target=app_main, view=ft.AppView.FLET_APP)

if __name__ == "__main__":
    main()