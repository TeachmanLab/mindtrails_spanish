import csv
import json

from pathlib import Path
from itertools import islice
from collections import defaultdict

import numpy as np

# leaving this seed unchanged means
# that huge diff won't be generated
# every time the output of these
# scripts is deployed. This state 
# needs to be global in order for 
# participants to experience the
# order of answers as random.
rng = defaultdict(lambda: np.random.RandomState(1))

def write_output(dir_out, structure):
    for path, content in structure.items():
        path = Path(f"{dir_out}/{path}")

        if path.suffix == ".json" and isinstance(content,dict):
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
            continue

        if path.suffix != ".json" and isinstance(content,list):
            path.mkdir(parents=True, exist_ok=True)
            for i,page in enumerate(content,1):
                with open(f"{path}/{i}.json", 'w', encoding='utf-8') as f:
                    json.dump(page, f, indent=4, ensure_ascii=False)
            continue

        raise Exception()

def get_groupnames():
    yield 'treatment'
    yield 'control'

def dir_safe(text):
    return text.replace("/","%2F").replace("\\","%5C").replace("+","%2B")

def is_int(val):
    try:
        int(val)
    except ValueError:
        return False
    else:
        return True

def is_yesno(values):
    return set([v.lower() for v in values]) in [set(["si", "no"]),set(["yes","no"])]

def has_value(value):
    return value and value.upper() not in ["NA","N/A","N\\A"]

def clean_up_unicode(text):
    if not text: return ""
    return text.replace("\u00e2\u20ac\u2122", "'").replace("\u2026", "...").replace("\u2013", " - ") \
        .replace("\u2014", " - ").replace("\u201c", '"').replace("\u201d", '"').replace("\\n", "\n") \
        .replace("\u2019", "'").replace("\u00e1", "á").replace("\u00e9", "é").replace("\u00ed", "í") \
        .replace("\u00f3", "ó").replace("\u00fa", "ú").replace(u'\xf1', 'n').replace("\u00fc", "ü") \
        .replace("\u00c1", "Á").replace("\u00c9", "É").replace("\u00cd", "Í").replace("\u00d3", "Ó") \
        .replace("\u00da", "Ú").replace("\u00d1", "Ñ").replace("\u00dc", "Ü").replace("  ", " ").strip()

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def get_resources(file_path):
    """A function that reads in the file of resources and outputs a dictionary with the resources for each domain

    :param file_path: string path to resources file (.csv)
    :return: dictionary {"Domain" : [index, [ [resource, text], [resource, text]...] ] }
        * keys (str) = domains
        * fields (list) = [index, domain_list_of_resources]
        * domain_list_of_resources (list of lists) = [[resource_1, text_1], [resource_2, text_2]]
            * each list WITHIN the list is [resource, text]

    File I used to make this: https://docs.google.com/spreadsheets/d/1kenROWNI498AcMhjElrFQD9IjOmnVGInVB8BShSYSx8/edit#gid=437897459
    """

    domain_indexes = [1, 3, 5, 7, 9, 11, 13, 15]
    domain_resources = [ [] for _ in domain_indexes ]

    with open(file_path, 'r', encoding='utf-8') as f:

        reader = csv.reader(f)
        domains = list(map(next(reader).__getitem__,domain_indexes))

        for i,row in enumerate(islice(reader,1,None),1):
            for resources, domain_index in zip(domain_resources, domain_indexes):
                res = row[domain_index]
                text = row[domain_index+1].strip() + "\n\n Vaya a la libreria de recursos disponibles para obtener el enlace a este recurso."
                if res: resources.append([res, text])

        return dict(zip(domains,domain_resources))

def get_ER(file_path):
    """A function that reads in the file of emotion regulation tips and outputs a dictionary with the ER tips for
    each domain

        :param file_path: string path to ER tips file (.csv)
        :return: dictionary {"Domain" : [index, [ [resource, text], [resource, text]...] ] }
            * keys (str) = domains
            * fields (list) = [index, domain_list_of_ER_tips]
            * domain_list_of_ER_tips (list of lists) = [[Estrategia de Regulación Emocional # 1, text_1], [Estrategia de Regulación Emocional# 2, text_2]]
                * each list WITHIN the list is [Estrategia de Regulación Emocional # 1, text]

        File I used to make this: https://docs.google.com/spreadsheets/d/1kenROWNI498AcMhjElrFQD9IjOmnVGInVB8BShSYSx8/edit#gid=0
        """

    domain_indexes = [1, 2, 3, 4, 5, 6, 7, 8]
    domain_strats = [ [] for _ in domain_indexes ]

    with open(file_path, 'r', encoding='utf-8') as f:

        reader = csv.reader(f)
        domain_names = list(map(next(reader).__getitem__,domain_indexes))

        for i,row in enumerate(reader,1):
            for strats, domain_index in zip(domain_strats, domain_indexes):
                if row[domain_index]: strats.append([f"Estrategia de Regulación Emocional #{i}", row[domain_index]])

        return dict(zip(domain_names,domain_strats))

def get_tips(file_path):
    """ Function that reads in the tips file and outputs a list of the tips

    :param file_path:
    :return: list of lists,[ [Tip #1, text], [Tip #2, text]...]

    https://docs.google.com/spreadsheets/d/1kenROWNI498AcMhjElrFQD9IjOmnVGInVB8BShSYSx8/edit#gid=2086298502
    """

    tips = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i,row in enumerate([r for r in islice(csv.reader(f),1,None) if r[1]]):
            tips.append([f"Consejo #{i}", row[1]]) # changed
    return tips

def create_puzzle(scenario):

    if not has_value(scenario): return None, None
    punctuation_marks = "?.!"

    puzzle_text = scenario
    last_word   = scenario.split()[-1].strip().strip(punctuation_marks)
    puzzle_word = last_word

    puzzle_text = rreplace(puzzle_text, f" {puzzle_word}", "..", 1)

    return puzzle_text, puzzle_word

def shuffle(items,key=None):
    rng[key].shuffle(items)

def lower(str):
    return str.lower() if str else ""

def media_url(media):
    if media and media.strip():
        assert Path(f"./src/images/{media.strip()}").exists()
        return f"./images/{media.strip()}"
    return ""

def get_page_index(scenario, session, position):
    curr_num  = None
    scn_index = 0
    neg_index = 0

    scenario = lower(scenario).strip()

    for i, page in enumerate(session):
        if curr_num != page["scenario_num"]:
            curr_num = page["scenario_num"]
            scn_index += 1
            neg_index += int(page.get("type") == "negative")

            if position == "before":
                if scenario == "first negative" and neg_index == 1:
                    return i
                if scenario != "first negative" and scn_index == int(scenario[8:]):
                    return i

            if position == "after":
                if scenario == "first negative" and neg_index == 1 and page.get("type") != "negative":
                    return i-1
                if scenario != "first negative" and scn_index == int(scenario[8:])+1:
                    return i-1

    if position == "after" and scenario != "first negative" and scn_index == int(scenario[8:]):
        return i

    return None

def get_reminder_element(reminder,position,count):
    if not reminder.strip(): return None
    is_image = ".png" in reminder or ".jpg" in reminder or ".jpeg" in reminder
    element = {"type":"text", "text": reminder} if not is_image else {"type":"media", "url": media_url(reminder)}
    return { "elements": [ element ], "position": position, "information_count": count }
