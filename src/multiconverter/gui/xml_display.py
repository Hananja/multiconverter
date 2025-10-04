# src/multiconverter/gui/xml_display.py
"""
Widget für die Anzeige von XML mit Syntax-Highlighting
"""
import flet as ft
import xml.dom.minidom as minidom

class XMLDisplayWidget:
    def __init__(self, xml_content: str):
        self.xml_content = xml_content

    def build(self) -> ft.Control:
        """Erstellt das XML Display Widget"""
        formatted_xml = self.format_xml(self.xml_content)

        return ft.Container(
            content=ft.Column([
                ft.Text("XML Vorschau:", style=ft.TextThemeStyle.LABEL_LARGE),
                ft.TextField(
                    value=formatted_xml,
                    multiline=True,
                    read_only=True,
                    min_lines=10,
                    max_lines=15,
                    border=ft.InputBorder.OUTLINE
                )
            ]),
            bgcolor=ft.colors.GREY_100,
            padding=10,
            border_radius=5
        )

    def format_xml(self, xml_string: str) -> str:
        """Formatiert XML für bessere Lesbarkeit"""
        try:
            dom = minidom.parseString(xml_string)
            return dom.toprettyxml(indent="  ")
        except Exception:
            return xml_string