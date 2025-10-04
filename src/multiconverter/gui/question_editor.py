# src/multiconverter/gui/question_editor.py
"""
Editor für einzelne Fragen mit XML Syntax-Highlighting und Validierung
"""
import flet as ft
import xml.etree.ElementTree as ET
from typing import List, Callable, Any
from ..xml_validator import XMLValidator

class QuestionEditorView:
    def __init__(self, page: ft.Page, questions: List[Any],
                 on_question_processed: Callable, on_all_processed: Callable):
        self.page = page
        self.questions = questions
        self.on_question_processed = on_question_processed
        self.on_all_processed = on_all_processed
        self.current_question_index = 0
        self.xml_validator = XMLValidator()

    def build(self):
        """Erstellt die Editor-Ansicht"""
        if not self.questions:
            return ft.Text("Keine Fragen zum Bearbeiten verfügbar")

        question = self.questions[self.current_question_index]
        question_xml = ET.tostring(question, encoding='unicode')

        editor_field = ft.TextField(
            label=f"Frage {self.current_question_index + 1} von {len(self.questions)}",
            multiline=True,
            min_lines=15,
            max_lines=20,
            value=question_xml,
            expand=True
        )

        return ft.Column([
            ft.Text("Schritt 3: Fragen bearbeiten", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text(f"Bearbeiten Sie die Frage {self.current_question_index + 1} von {len(self.questions)}:"),
            editor_field,
            ft.Row([
                ft.ElevatedButton(
                    "Sichern",
                    on_click=lambda _: self.save_question(editor_field.value),
                    icon=ft.icons.SAVE,
                    color=ft.colors.GREEN
                ),
                ft.ElevatedButton(
                    "Verwerfen",
                    on_click=lambda _: self.discard_question(),
                    icon=ft.icons.DELETE,
                    color=ft.colors.RED
                )
            ])
        ])

    def save_question(self, xml_content: str):
        """Sichert die bearbeitete Frage"""
        try:
            # Validiere das bearbeitete XML
            validation_result = self.xml_validator.validate_xml_string(xml_content)
            if not validation_result.is_valid:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"XML Fehler: {validation_result.error_message}"))
                )
                return

            # Parse das XML
            question = ET.fromstring(xml_content)
            self.on_question_processed(question, "save")
            self.next_question()

        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Fehler beim Sichern: {str(e)}"))
            )

    def discard_question(self):
        """Verwirft die aktuelle Frage"""
        self.on_question_processed(self.questions[self.current_question_index], "discard")
        self.next_question()

    def next_question(self):
        """Geht zur nächsten Frage oder beendet die Bearbeitung"""
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            self.on_all_processed()
        else:
            self.page.clean()
            self.page.add(self.build())
            self.page.update()