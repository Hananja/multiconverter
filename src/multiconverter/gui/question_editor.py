# src/multiconverter/gui/question_editor.py
"""
Editor für einzelne Fragen mit XML Syntax-Highlighting und Validierung
"""
import os

import flet as ft
import xml.etree.ElementTree as ET
from typing import List, Callable, Any
from ..xml_validator import XMLValidator

# Template-Verzeichnis relativ zum Skript finden
script_dir = os.path.dirname(os.path.abspath(__file__))
xsd_path = os.path.join(script_dir, "../xml/llmquestions.xsd")

ET.register_namespace("", "https://github.com/Hananja/multiconverter")

class QuestionEditorView:
    def __init__(self, page: ft.Page, questions: List[Any],
                 on_question_processed: Callable, on_all_processed: Callable):
        self.editor_field = None
        self.page = page
        self.questions = questions
        self.on_question_processed = on_question_processed
        self.on_all_processed = on_all_processed
        self.current_question_index = 0
        self.xml_validator = XMLValidator(xsd_path)

    def build(self):
        """Erstellt die Editor-Ansicht"""
        if not self.questions:
            return ft.Text("Keine Fragen zum Bearbeiten verfügbar")

        self.editor_field = ft.TextField(
            multiline=True,
            min_lines=10,
            max_lines=20,
            expand=True
        )
        self.update_editor_field()

        return ft.Column([
            ft.Text("Schritt 3: Fragen bearbeiten:"),
            self.editor_field,
            ft.Row([
                ft.ElevatedButton(
                    "Sichern",
                    on_click=lambda _: self.save_question(self.editor_field.value),
                    icon=ft.Icons.SAVE,
                    color=ft.Colors.GREEN
                ),
                ft.ElevatedButton(
                    "Verwerfen",
                    on_click=lambda _: self.discard_question(),
                    icon=ft.Icons.DELETE,
                    color=ft.Colors.RED
                )
            ])
        ])

    def save_question(self, xml_content: str):
        """Sichert die bearbeitete Frage"""
        try:
            # Validiere das bearbeitete XML
            validation_result = self.xml_validator.validate_xml_string(xml_content)
            if not validation_result.is_valid:
                snack_bar = ft.SnackBar(content=ft.Text(f"XML Fehler: " + os.linesep.join(
                    map(lambda x:x[1], validation_result.errors))))
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
                return

            # Parse das XML
            question = ET.fromstring(xml_content)
            self.on_question_processed(question, "save")
            self.next_question()

        except OSError as e:
            snack_bar = ft.SnackBar(content=ft.Text(f"Fehler beim Sichern: {str(e)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()

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
            self.update_editor_field()

    def update_editor_field(self):
        """Aktualisiert das Editor-Feld mit dem aktuellen XML-Inhalt"""
        if self.editor_field:
            question = self.questions[self.current_question_index]
            question_xml = ET.tostring(question, encoding='unicode')
            self.editor_field.value = question_xml
            self.editor_field.label = f"Frage {self.current_question_index + 1} von {len(self.questions)}"
            self.page.update()

