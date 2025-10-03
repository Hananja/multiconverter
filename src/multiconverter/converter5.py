# commandline tool to display help when called without parameters and process all given files otherwise from parameters
import io, sys, os
import zipfile
import jinja2
from dataclasses import dataclass
from uuid import uuid4
from itertools import starmap

from multiconverter.tools import include_min_xsd_file, get_local_tag, escape_content_data
from multiconverter.xml_validator import XMLValidator, Error

# Template-Verzeichnis relativ zum Skript finden
script_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(script_dir, 'templates')
xsd_path = os.path.join(script_dir, "xml/llmquestions.xsd")

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    # autoescape=jinja2.select_autoescape(['html', 'xml']),
    undefined=jinja2.StrictUndefined
)
jinja_env.globals['include_min_xsd_file'] = include_min_xsd_file

xmlns = {"m":"https://github.com/Hananja/multiconverter"}

def die(message):
    """ Print the message and let the process die afterward """
    print(message)
    sys.exit(1)

@dataclass
class QuestionFragments:
    item_text: str
    manifest_text: str

class QuestionHandlers:
    def __init__(self):
        self.identity_counter : int = 1
        self.items_map : dict[str, QuestionFragments] = {} # key is id

    def handle_multiple_choice_question(self, question):
        item_context, manifest_context = self._prepare_context()
        if 1 == sum(1 for option in question.find('./m:options', xmlns) if option.attrib['correct'] == 'true'):
            item_context['cardinality'] = "single"
            item_context['max_choices'] = "1"
            item_context['title'] = "MultipleChoice"
        else:
            item_context['cardinality'] = "multiple"
            item_context['max_choices'] = "0"
            item_context['title'] = "MultipleResponse"
        manifest_context['title'] = item_context['title']  # without ... etc.
        question_text = escape_content_data(question.find('./m:text', xmlns).text)
        item_context['title'] += ": " + question_text[:20] + "..." if len(question_text) > 20 else ""
        item_context['question_html'] = question_text
        item_context['choices'] = starmap(lambda i, option: (
            "plus" if option.attrib['correct'] == 'true' else "minus",
            escape_content_data(option.text)
        ), enumerate(question.find('./m:options', xmlns).findall('./m:option', xmlns)))
        manifest_context['interaction_type'] = 'choiceInteraction'

        self._add_item(item_context, manifest_context, "choiceInteraction")

    def handle_fill_in_question(self, question):
        item_context, manifest_context = self._prepare_context()
        manifest_context['title'] = "FillInTheBlankText"
        manifest_context['interaction_type'] = 'textEntryInteraction'
        question_text = question.find('./m:text', xmlns).text if question.find('./m:text', xmlns) is not None else None
        item_context['title'] = ("FillInTheBlankText: " + question_text[:20] if question_text else ""
                                  + "..." if question_text and len(question_text) > 20 else "" )
        item_context['question_html'] = escape_content_data(question_text)
        item_context['responses_map'] = {}
        fill_in = question.find('./m:fill-in-text', xmlns)
        fill_in_text = fill_in.text if fill_in.text is not None else ""
        for response_counter, fill in enumerate(fill_in):
            response_identifier = f'RESPONSE{response_counter:02}'
            item_context['responses_map'][response_identifier] = list(map(lambda x:x.text,
                                                                          fill.findall('./m:alt', xmlns)))
            fill_in_text += f'<textEntryInteraction responseIdentifier="{response_identifier}"/>'
            fill_in_text += fill.tail if fill.tail is not None else ""  # following text
        item_context['fill_in_html'] = escape_content_data(fill_in_text)

        self._add_item(item_context, manifest_context, "textEntryInteraction")

    def handle_map_question(self, question):
        item_context, manifest_context = self._prepare_context()
        item_context['title'] = "Matching"
        manifest_context['title'] = item_context['title']
        manifest_context['interaction_type'] = 'matchInteraction'
        item_context['question_html'] = escape_content_data(question.find('./m:text', xmlns).text)
        item_context['choice_count'] = len(question.findall('./m:mappings/m:mapping', xmlns))
        item_context['left_choices'] = enumerate(map(
            lambda x:x.text, question.findall('./m:mappings/m:mapping/m:left', xmlns)))
        item_context['right_choices'] = enumerate(map(
            lambda x: x.text, question.findall('./m:mappings/m:mapping/m:right', xmlns)))

        self._add_item(item_context, manifest_context, "mapInteraction")

    def _add_item(self, item_context, manifest_context, question_type_id):
        self.items_map[item_context['assessment_identifier']] = QuestionFragments(
            item_text=jinja_env.get_template(f"assessmentItem_{ question_type_id }.xml.jinja").render(**item_context),
            manifest_text=jinja_env.get_template("imsmanifest_resource.xml.jinja").render(**manifest_context),
        )

    def _prepare_context(self):
        item_context, manifest_context = {}, {}
        item_context['assessment_identifier'] , manifest_context['resource_identifier'] = self._get_identifiers()
        manifest_context['resource_href'] = item_context['assessment_identifier'] + ".xml"
        return item_context, manifest_context


    question_handlers_map = {  # xml-tag: func
        "multiple-choice-question": handle_multiple_choice_question,
        "fill-in-question": handle_fill_in_question,
        "map-question": handle_map_question,
    }
    def handle_question(self, question):
        self.question_handlers_map[get_local_tag(question)](self, question)

    def _new_identifier(self):
        identifier = f"item-{self.identity_counter:05}"
        self.identity_counter += 1
        return identifier

    def _get_identifiers(self):
        identifier = self._new_identifier()
        return identifier, f"resource-{identifier}"

    def get_zip(self) -> bytes:
        zip_buffer = io.BytesIO()
        # from converter4.py
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for identifier, item in self.items_map.items():
                with zipf.open(f'{identifier}.xml', 'w') as file:
                    file.write(item.item_text.encode('utf-8'))
            with zipf.open('imsmanifest.xml', 'w') as file:
                file.write(self.generate_manifest().encode('utf-8'))
        return zip_buffer.getvalue()

    def generate_manifest(self):
        context = {}
        context['manifest_identifier'] = f"llm-multiconverter-{uuid4()}"
        context['resources'] = map(lambda x:x.manifest_text, self.items_map.values())
        return jinja_env.get_template("imsmanifest.xml.jinja").render(**context)


def main(argv):
    if len(argv) < 3:
        die(jinja_env.get_template("help.txt.jinja").render())
        return # never reached outside stubbed test mode

    output_filename = argv[1]
    input_filenames = argv[2:]
    validator = XMLValidator(xsd_path)
    validation_results = validator.validate_files(input_filenames)
    if not all(map(lambda x:x.is_valid, validation_results.values())):
        handle_error(validation_results)
    else:
        handlers = QuestionHandlers()
        for filename in input_filenames:
            xml = validation_results[filename].xml_content
            if get_local_tag(xml) == 'questions':
                for question in xml:
                    handlers.handle_question(question)
            else: # single question as root
                handlers.handle_question(xml)
        result = handlers.get_zip()
        with open(output_filename, 'wb') as file:
            file.write(result)



def handle_error(validation_results):
    for filename, document in validation_results.items():
        if document.is_valid:
            print(f"Gültig: {filename} Root-Tag: {document.xml_content.tag}")
        else:
            print(f"Ungültig: {filename}")
            for error, error_message in document.errors:
                if error in (Error.XSD_ERROR, Error.XML_ERROR):
                    die(jinja_env.get_template("error_xsd.txt.jinja").render(file=filename, error=error_message))
                else:
                    die(error_message)


if __name__ == '__main__':
    main(sys.argv)
