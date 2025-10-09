# Add more question types

1. Download demo file from old test in itslearning
2. Build template for item (`templates/assessmentItem_*`)
3. Extend XSD `xml/llmquestions.xsd` with new question type (Note: use only one top level element per question type
   because of filtering in gui)
4. Create context handler `handle_xxx` to render templates and provide context in `coverter5.py`
5. Add handler function to `question_handlers_map` to associate it to the new defined tag in xsd.
6. extend GUI