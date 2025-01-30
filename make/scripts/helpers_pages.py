import csv
import random

from itertools import islice

from helpers_utilities import get_lessons_learned_text, clean_up_unicode, has_value, is_yesno, is_int

random.seed(1) #give a fixed seed so that diffs don't make it look like we changed a lot every time we generate

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
file_path = f"{dir_csv}/Spanish lessons_learned_text.csv"

lessons_learned_dict = get_lessons_learned_text(file_path)

def create_condition(args):
    if args == [''] or not args: return None
    variable, value = [a.strip() for a in args]
    if ',' in value: value = [int(v) for v in value.split(",") if is_int(v)]
    comparison = "=" if not isinstance(value,list) else "in"
    return { "variable": variable, "comparator": comparison, "value": value }

def create_input(tipe, items=None, min=None, max=None, text=None):
    if not tipe: return None

    if items: items = clean_up_unicode(items).split("; ")
    if items == [""]: items = None

    ## Based on what the input is, create input "add"
    if tipe == "Picker"   : return {"type": "Picker", "items": items}
    if tipe == "Slider"   : return {"type": "Slider", "min": min, "max": max, "others": items or ["^Prefiero no responder"]} # changed
    if tipe == "Entry"    : return {"type": "Entry" }
    if tipe == "Buttons"  : return {"type": "Buttons", "buttons": items, "selectable": True, **({"ColumnCount": 2} if is_yesno(items) else {}) }
    if tipe == "Scheduler": return {"type": "scheduler", "message": "¡Es hora de practicar el pensamiento flexible! Dirígete a MindTrails Español para tu sesión programada."}
    if tipe == "Checkbox" : return {"type": "buttons", "buttons": items, "selectable": True, "multi_select": True }
    if tipe == "TimedText": return {"type": "TimedText", "text": text,  "Duration": 15 }
    if tipe == "Puzzle"   : return {
        "type": "WordPuzzle",
        "right_feedback": "Correcto!",  # changed
        "wrong_feedback": "¡Vaya! Eso no parece correcto. Por favor, espere un momento y intenta de nuevo.",  # changed
        "wrong_delay": 5000,
        "cause_navigation": True,
        "words": items
    }
    return None

def create_long_pages(label, scenario_description, unique_image, thoughts, feelings, behaviors):
    """
    :param unique_image: Bool, False means that the photos for each group are all the same
    :param label: The title of the long scenario
    :param scenario_description: The text for the scenario
    :param thoughts: list of thoughts to show for long scenarios
    :param feelings: list of feelings to show for long scenarios
    :param behaviors: list of behaviors to show for long scenarios
    :return: a page group for the long scenario
    """
    
    pages = []
    label = label.strip()

    with open(f"{dir_csv}/Spanish htc_long_scenarios_structure.csv","r", encoding="utf-8") as csvfile:
        for row in islice(csv.reader(csvfile),1,None):

            input_1, is_image, timeout = row[6], row[10]=="TRUE", row[13]

            title = row[0].replace("[Scenario_Name]", label)
            descr = clean_up_unicode(row[4].replace("[Scenario_Description]", scenario_description))

            if unique_image:
                image_url = f"/images/{label.replace(' ', '_')}.jpg"
            else:
                image_url = f"/images/{label.replace(' ', '_')}.jpg"

            text  = {"type": "Text", "text": descr}
            media = {"type": "Media", "frame": True, "path": image_url} if is_image else None

            timeout = {"timeout": int(timeout) } if timeout else {}

            show_buttons = {}
            if input_1 == "TimedText":
                show_buttons = {"show_buttons": "WhenCorrect" }
            elif timeout:
                show_buttons = {"show_buttons": "AfterTimeout" }

            text = None
            if "pensamientos" in descr:
                text = thoughts
            elif "sentimientos" in descr:
                text = feelings
            elif "comportamientos" in descr:
                text = behaviors

            input = create_input(input_1,text=text)

            pages.append({"title": title, "name": label, "elements": list(filter(None,[text,media,input])), **show_buttons, **timeout })

    return pages

def create_scenario_pages(domain, label, scenario_num, puzzle_text_1, word_1, comp_question,
                          answers, correct_answer, unique_image, row_num, word_2=None,
                          puzzle_text_2=None, letters_missing=1, lessons_learned=False,
                          lessons_learned_dict=lessons_learned_dict):
    """
    :param unique_image: Bool, False means that the photos for each group are all the sameunique
    :param domain: domain (e.g., "Romantic Relationships" or "Physical Health")
    :param label:
    :param scenario_num:
    :param puzzle_text_1: text for the first puzzle
    :param word_1: missing word for the first puzzle
    :param comp_question: comprehension question
    :param answers: list of possible answers to the comprehension question
    :param correct_answer: correct answer from answers
    :param row_num:
    :param word_2: missing word for the second puzzle
    :param puzzle_text_2: text for the second puzzle
    :param letters_missing:
    :param lessons_learned:
    :param lessons_learned_dict:
    :return:
    """

    is_first_scenario = (int(row_num) - 1) % 10 == 0
    pages = []

    if lessons_learned:  # if it should include a "lessons learned" page
        pages.append({
            "name": f"Lessons Learned{row_num}",
            "title": "Lecciones Aprendidas",  # changed
            "elements": [
                {"type": "Text","Text": clean_up_unicode(lessons_learned_dict[domain])},
                {"type": "Entry", "name": f"lessons_learned_{domain}_{scenario_num}"}
            ]
        })

    if letters_missing == "all" and is_first_scenario:
        # if all letters missing, and it's the first scenario, add an instructions page
        pages.append({
            "name": f"{label} Instructions",
            "title": "Instrucciones",  # changed
            "elements": [{
                "type": "Text",
                "text": "Las historias que estás a punto de ver son un poco diferentes a las que has visto"
                        "visto antes. En lugar de completar las letras que faltan para completar la palabra final,"
                        "Vamos a desafiarte a generar tu propia última palabra que completará"
                        "la historia. Tu objetivo es pensar en una palabra que terminará la historia en un "
                        "nota positiva. El final no tiene por qué ser tan positivo como para no serlo"
                        "Parece posible, pero queremos que imagines que estás manejando bien la situación."
                        # changed
            }]
        })


    if unique_image:
        image_url = f"/images/{label.strip().replace(' ','_')}.jpg"
    else:
        image_url = f"/images/{label.strip().replace(' ', '_')}.jpg"

    pages.append({  # adding the image page
        "name": f"{label}{row_num}",
        "title": label,
        "elements": [
            {"type": "Label", "text": label },
            {"type": "Media", "file": image_url }
        ]
    })

    pages.append({  # adding the puzzle page
        "name": "Puzzle",
        "title": label,
        "elements": [
            {"type": "Text", "text": puzzle_text_1},
            {
                "type": "WordPuzzle",
                "name": f"{label}_{domain}_puzzle1",
                "correct_feedback": "Correcto!",  # changed
                "incorrect_feedback": "¡Vaya! Eso no parece correcto. Por favor, espere un momento "
                                      "y intenta de nuevo.",  # changed
                "incorrect_delay": 5000,
                "cause_navigation": True,
                "words": [word_1]
            }
        ]
    })

    if letters_missing in ["1","2"]:
        pages[-1]["elements"][-1]["missing_letter_count"] = int(letters_missing)
    elif letters_missing == "all":
        pages[-1]["elements"][-1] = {"type": "Entry", "name": f"{label}_{domain}_entry1" }

    if has_value(word_2) and has_value(puzzle_text_2):
        pages.append({
            "name": "Puzzle 2",
            "title": label,
            "elements": [
                {"type": "Text", "text": puzzle_text_2},
                {
                    "type": "WordPuzzle",
                    "name": f"{label}_{domain}_puzzle_word2",
                    "correct_feedback": "Correcto!",  # changed
                    "incorrect_feedback": "¡Vaya! Eso no parece correcto. Por favor, espere un momento "
                                          "y intenta de nuevo.",  # changed
                    "incorrect_delay": 5000,
                    "cause_navigation": True,
                    "words": [word_2]
                }
            ]
        })

        if letters_missing in ["1","2"]:
            pages[-1]["elements"][-1]["missing_letter_count"] = int(letters_missing)
        elif letters_missing == "all":
            pages[-1]["elements"][-1] = {"type": "Entry", "name": f"{label}_{domain}_entry2" }

    if letters_missing != "all":
        pages.append({
            "name": "Question",
            "title": label,
            "show_buttons": "WhenCorrect",
            "elements": [
                { "type": "Text", "Text": comp_question},
                {
                    "type": "Buttons",
                    "name": f"{label}_{domain}_comp_question",
                    "correct_feedback": "Correcto!",  # changed
                    "incorrect_feedback": "¡Vaya! Eso no parece correcto. Por favor, espere un momento "
                                          "y intenta de nuevo.",  # changed
                    "incorrect_dealy": 5000,
                    "buttons": answers,
                    "columnCount": 1,
                    "answer": correct_answer
                }
            ]
        })

    return pages

def create_resource_page(resources_lookup, tips, ER_lookup, domain):
    """
    Create a resource page group (Resource, ER strategy, or Tip)
    :param resources_lookup: Object created by get_resources()
    :param tip: List created by get_tips()
    :param ER_lookup: Object created by get_ER()
    :param domain: the domain
    :return: a page group for a resource, ER strategy, or tip
    """
    
    resource_type = random.choice(["Resource", "Tip", "ER Strategy"])

    if resource_type == "Resource":
        label,text = resources_lookup[domain].pop(0)  # resource name and text
        resources_lookup[domain].append([label,text])   # place at back
        text = f"{label}\n\n{text}"

        title = f"Recurso: {domain}"# changed
        name =  label
        input  = None

    if resource_type == "Tip":
        label,text = tips.pop(0)  # pop the first list within the lists out of tip
        tips.append([label,text])  # adding that tip back to the end of the list

        title = "Aplicar a la vida diaria: ¡Haz que funcione para ti!"  # changed
        name  = "¡Consejo para aplicar!" # changed
        input = {"type": "Entry", "name": f"{label}_entry"}

    if resource_type == "ER Strategy":
        [label,text] = ER_lookup[domain].pop(0)  # popping the first list of lists
        ER_lookup[domain].append([label,text])  # adding it back to the end of the list of lists

        title = f"Maneja tus sentimientos: {domain}" # domain name  # changed
        name  = "Consejo para la regulación de las emociones"  # changed
        input = None

    text = { "type": "Text", "text": text }
    elements = [text,input] if input else [text]

    return {"title": title, "name": name, "elements": elements }

def create_discrimination_page(conditions, text, items, input_1,
                               input_name, title):

    condition = create_condition(conditions)
    text = {"type": "Text", "text": text}

    input = create_input(input_1, items)
    if input: input["name"] = input_name

    elements = [text,input] if input else [text]
    page = { "title": title, "elements": elements }

    if condition: page["conditions"] = [condition]

    return page

def create_survey_page(text=None, media=None, image_framed=None, items=None, input_1=None, input_2=None,
                       variable_name=None, title=None, input_name=None, minimum=None, maximum=None,
                       show_buttons=None, conditions=None, timeout=None):
    """
    This function creates a page with a survey question.
    :param text: Text to go on the page
    :param media: Link to image or video that should be shown on that page
    :param image_framed: True/False if the image should be framed in the middle of the page (as opposed to taking up the entire screen)
    :param items: Options for buttons, or other text options ("OtherChoices") for slider questions (usually 'Prefer not to answer')
    :param input_1:  Buttons, Picker, Checkbox, Puzzle, Entry, Slider, Scheduler
    :param input_2: Second input on the page:  Buttons, Picker, Checkbox, Puzzle, Entry, Slider, Scheduler
    :param variable_name: If later pages being shown depend on the answer to this page, you need to set a VariableName for it
    :param title: title of the page
    :param input_name: the name that will pair with the survey question when the participant's data from the app is downloaded. This is very important to have for each page that you want to save a participant's response to
    :param minimum: minimum value for sliders
    :param maximum: maximum value for sliders
    :param show_buttons: "WhenCorrect" if next button is shown only after the participant answers it correctly,
                         "AfterTimeout" if next button is shown after a certain time (timeout) has happened,
                         "Never" if the next button is never shown, &  the page will automatically go to next page after timeout
    :param conditions: conditions that need to be met to view the page. For example
                            "StressLevel; 6, 7" will be parsed to ["StressLevel", "6, 7"]
                            The first item in the list is the VariableName, the second item are the answers that need
                            to have been selected in order for teh page to appear.
                            In this case, someone has to pick "6" or "7" for the StressLevel question in order to
                            see the page
    :param timeout: see show_buttons "AfterTimeout"
    :return: a page for a survey question / text page
    """

    textinput  = {"type": "Text", "text": text} if has_value(text) else None
    mediainput = {"type": "Media", "path": media, "frame": image_framed == "TRUE"} if media else None

    input1 = create_input(input_1, items, minimum, maximum)
    input2 = create_input(input_2, items, minimum, maximum)

    if input1: input1["name"] = input_name if input_1 != 'Scheduler' else 'schedule_session'
    if input2: input2["name"] = input_name if input_2 != 'Scheduler' else 'schedule_session'

    if variable_name and input1: input1["variable_name"] = variable_name
    if variable_name and input2: input2["variable_name"] = variable_name

    condition = create_condition(conditions)

    timeout      = {"timeout"    : int(timeout) } if timeout else {}
    show_buttons = {"show_buttons": show_buttons } if show_buttons and timeout else {}
    condition    = {"conditions" : [condition]  } if condition else {}

    elements = list(filter(None, [textinput, mediainput, input1, input2] ))
    page     = { "title": title, "elements": elements, **timeout, **show_buttons, **condition }

    return page
