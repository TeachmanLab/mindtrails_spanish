import csv
import shutil
import json

from collections import defaultdict
from itertools import islice, chain
from pathlib import Path

from helpers_pages import create_survey_page
from helpers_utilities import clean_up_unicode, write_output, media_url

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def flat(dictionary):
    return list(chain.from_iterable(dictionary.values()))

def _create_survey_page(row):
    text = clean_up_unicode(row[4])

    title = row[1].strip()
    input_1 = row[5]
    input_2 = row[6]
    minimum = row[7]
    maximum = row[8]
    media = media_url(row[9])
    items = row[10]
    image_framed = row[11]
    timeout = row[12]
    show_buttons = row[13]
    variable_name = row[16]
    conditions = row[17]
    input_name = row[18]

    return create_survey_page(conditions=conditions, text=text,
                                show_buttons=show_buttons, media=media, image_framed=image_framed,
                                items=items, input_1=input_1, input_2=input_2,
                                variable_name=variable_name, title=title, input_name=input_name,
                                minimum=minimum, maximum=maximum, timeout=timeout)

# Read the questions
survey_pages = defaultdict(lambda: defaultdict(list))
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

        if row[2] and row[0] != "Práctica CBM-I": survey_pages[group_id][subgroup_id].append(_create_survey_page(row))

# Define folders
folders = {
    "treatment/final del dia": flat(survey_pages[("all","eod")]),
    "treatment/reasons for ending": flat(survey_pages[("all","reasonsforending")]),
    "treatment/sigue tu progreso/__flow__.json": {"mode":"sequential","take":1},
    "treatment/sigue tu progreso/1": flat(survey_pages[("all","biweekly")]) + flat(survey_pages[("2","biweekly")]),
    "treatment/sigue tu progreso/2": flat(survey_pages[("all","biweekly")]) + flat(survey_pages[("4","biweekly")]),
    "treatment/sigue tu progreso/3": flat(survey_pages[("all","biweekly")]) + flat(survey_pages[("6","biweekly")]),
    "treatment/sigue tu progreso/4": flat(survey_pages[("all","biweekly")]) + flat(survey_pages[("8","biweekly")]),
    "control/final del dia": flat(survey_pages[("all","eod")]),
    "control/reasons for ending": flat(survey_pages[("all","reasonsforending")]),
    "control/sigue tu progreso/__flow__.json": {"mode":"sequential","take":1},
    "control/sigue tu progreso/1": flat(survey_pages[("2","biweekly_control")]),
    "control/sigue tu progreso/2": flat(survey_pages[("4","biweekly_control")]),
    "control/sigue tu progreso/3": flat(survey_pages[("6","biweekly_control")]),
    "control/sigue tu progreso/4": flat(survey_pages[("8","biweekly_control")]),
}

# Delete old JSON
for key in folders.keys():
    shutil.rmtree(f"{dir_out}/{str.join('/',key.split('/')[:2])}",ignore_errors=True)

# Write new JSON
write_output(dir_out, folders)