import csv
import shutil
import json

from collections import defaultdict
from itertools import islice, chain, product
from pathlib import Path
import numpy as np

from helpers_pages import create_scenario_pages, create_survey_page
from helpers_utilities import clean_up_unicode, create_puzzle, get_groupnames, shuffle

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def get_relflows(groupname):
    return f"{groupname}/flows"

def get_relpages(groupname,flowname):
    return f"{groupname}/flows/{flowname}"

def get_flownames():
    yield 'intro'
    yield 'biweekly_2'
    yield 'biweekly_4'
    yield 'biweekly_6'
    yield 'biweekly_8'
    yield 'eod'
    yield 'reasons for ending'

def get_flowpages(flowname,groupname,survey_pages):

    #this part gets a little messy and has to be hard coded
    #all the possible options we care about are below
    # 1,dose               = intro for treatment
    # 1,control_dose       = intro for control
    # all,biweekly         = every biweekly for treatment
    # X,biweekly           = specific biweekly weeks for treatment
    # X,biweekly_control   = specific biweekly weeks for control
    # All,ReasonsForEnding = unenroll for treatment and control
    # All,EOD              = end of day for treatment

    flat = chain.from_iterable

    if flowname == "intro" and groupname == "treatment":
        yield from flat(survey_pages[("1","dose")].values())
        return

    if flowname == "intro" and groupname == "control":
        yield from flat(survey_pages[("1","control_dose")].values())
        return

    if flowname == "eod":
        yield from flat(survey_pages[("all","eod")].values())
        return

    if flowname == "reasons for ending":
        yield from flat(survey_pages[("all","reasonsforending")].values())
        return

    if flowname.startswith("biweekly") and groupname == "treatment":
        yield from flat(survey_pages[("all","biweekly")].values())
        yield from flat(survey_pages[(flowname[-1],"biweekly")].values())
        return

    if flowname.startswith("biweekly") and groupname == "control":
        yield from flat(survey_pages[("all","biweekly")].values())
        yield from flat(survey_pages[(flowname[-1],"biweekly_control")].values())

def create_video_page(video_number):
    return {
        "name": f"Video {video_number}",
        "elements": [
            {"type": "Text" , "text": "¡Presione play en el video de entrenamiento a continuación para obtener más información!"},
            {"type": "Media", "file": f"/videos/video{video_number}.mp4", "Frame": True}
        ]
    }

def _create_practice_pages():
    with open(f"{dir_csv}/Spanish_dose1_scenarios.csv", "r", encoding="utf-8") as dose1_read_obj:  # scenarios for first dose in file
        dose1_scenario_num = 0
        for row_1 in islice(csv.reader(dose1_read_obj),1,None):

            # First, add the video that goes before each scenario
            yield create_video_page(dose1_scenario_num+1)

            domain, label = row_1[0].strip(), row_1[3]
            puzzle1,puzzle2 = map(create_puzzle,row_1[4:6])
            question, choices, answer = row_1[6], row_1[7:9], row_1[7]

            shuffle(choices)

            # Create scenario page group for the practice
            yield from create_scenario_pages(domain=domain, label=label, scenario_num=dose1_scenario_num,
                                                    puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                                    comp_question=question, answers=choices,
                                                    correct_answer=answer, word_2=puzzle2[1],
                                                    puzzle_text_2=puzzle2[0], unique_image=False,
                                                    row_num=dose1_scenario_num)

            if dose1_scenario_num == 0:
                make_it_your_own_text =  "Queremos que MindTrails Español satisfaga sus necesidades. Cuando complete " \
                                            "sesiones de capacitación en la aplicación o buscar recursos en " \
                                            "biblioteca de recursos bajo demanda, verá un botón que parece " \
                                            "como una estrella en la esquina superior derecha de la pantalla. Por " \
                                            "haciendo clic en la estrella, puedes agregar la información que más te parezca " \
                                            "útil (por ejemplo, historias cortas, consejos para controlar el estrés) para su " \
                                            "propia página personal de Favoritos. Luego podrás volver a visitar tu favorito " \
                                            "partes de la aplicación cuando quieras eligiendo Favoritos " \
                                            "¡mosaico de la página de inicio de MindTrails Español!"  # changed

                page = create_survey_page(text=make_it_your_own_text, title="¡Hazlo tuyo!")  # changed
                page["name"] = "Make it your own!"
                yield page

            dose1_scenario_num += 1

def _create_survey_page(row):
    text = clean_up_unicode(row[4])

    title = row[1].strip()
    input_1 = row[5]
    input_2 = row[6]
    minimum = row[7]
    maximum = row[8]
    media = row[9]
    items = row[10]
    image_framed = row[11]
    timeout = row[12]
    show_buttons = row[13]
    variable_name = row[16]
    conditions = row[17].split('; ')
    input_name = row[18]

    return create_survey_page(conditions=conditions, text=text,
                                show_buttons=show_buttons, media=media, image_framed=image_framed,
                                items=items, input_1=input_1, input_2=input_2,
                                variable_name=variable_name, title=title, input_name=input_name,
                                minimum=minimum, maximum=maximum, timeout=timeout)

# The keys in this dictionary correspond to the HTC_survey_questions.csv lookup codes (<Doses>,<Subject>)
# You can see all the lookup codes and their meanings below:
# https://docs.google.com/spreadsheets/d/1Z_syG-HbyFT2oqMsHnAbidRtlH97IVxnBqbNKZWbwLY/edit#gid=0

survey_pages = defaultdict(lambda: defaultdict(list))

#Read the survey questions
with open(f"{dir_csv}/MTSpanish_survey_questions.csv", "r", encoding="utf-8") as read_obj:

    for row in islice(csv.reader(read_obj),1,None):

        # In *survey_questions.csv each row is a single question (aka, "page") in Digital Trails.
        # The "Subject" column indicates which script/flow type the question belongs to and the
        # "Dose" column indicates which run of the "Subject" flow the row belongs too.

        # One counter-intuitve aspect of this is the "Introduction" survey. This flow has a subject
        # of "Dose" (i.e., the same as the session microdoses). This is because the Intro flow is
        # a special flow that only occurs on the first microdose session. Therefore, intro flow
        # questions are all rows in *survey_questions.csv with Subject=Dose and Dose=1.

        # Each flow can be uniquely identified by the flow it
        # belongs to and which run of that flow it appears on

        dose        = row[2].lower()
        subject     = row[3].lower()
        group_id    = (dose,subject)
        subgroup_id = row[0]

        if row[0] == "Práctica CBM-I":
            survey_pages[group_id][subgroup_id].extend(_create_practice_pages())
        elif row[2]:
            survey_pages[group_id][subgroup_id].append(_create_survey_page(row))

#Create the surveys
for groupname,flowname in product(get_groupnames(),get_flownames()):

    root_dir = f"{dir_out}/{groupname}/flows"
    pages_dir = f"{root_dir}/biweekly/{int(flowname[-1])//2}" if "biweekly" in flowname else f"{root_dir}/{flowname}"

    shutil.rmtree(pages_dir,ignore_errors=True)

    Path(pages_dir).mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(get_flowpages(flowname, groupname, survey_pages),1):
        with open(f"{pages_dir}/{i}.json", 'w', encoding='utf-8') as f:
            json.dump(page, f, indent=4, ensure_ascii=False)

#Configure biweekly so they only get one survey at a time
for groupname in get_groupnames():
    biweekly_config_path = f"{dir_out}/{groupname}/flows/biweekly/__flow__.json"
    biweekly_config_json = {"mode":"sequential","size":1}
    with open(biweekly_config_path, 'w', encoding='utf-8') as f:
        json.dump(biweekly_config_json, f, indent=4, ensure_ascii=False)
