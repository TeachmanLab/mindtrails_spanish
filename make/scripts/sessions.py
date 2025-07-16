import csv
import shutil
import json

from collections import defaultdict
from itertools import islice, cycle, chain
from pathlib import Path

from helpers_pages import create_discrimination_page, create_scenario_pages, create_survey_page,create_resource_page
from helpers_pages import create_long_pages, create_write_your_own_page, create_video_page
from helpers_utilities import get_resources, get_ER, get_tips, clean_up_unicode, has_value, create_puzzle, dir_safe, shuffle, write_output, media_url, lower

dir_root = "./make"
dir_csv    = f"{dir_root}/CSV"
dir_out    = f"{dir_root}/~out"
dir_flows  = f"{dir_out}/treatment"
dir_doses  = f"{dir_flows}/doses"
dir_before = f"{dir_doses}/__before__"
dir_after  = f"{dir_doses}/__after__"
dir_after  = f"{dir_doses}/__first__"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def flat(dictionary):
    return list(chain.from_iterable(dictionary.values()))

def _create_practice_pages():
    with open(f"{dir_csv}/Spanish_dose1_scenarios.csv", "r", encoding="utf-8") as dose1_read_obj:  # scenarios for first dose in file
        
        scenario_num = 0
        for row in islice(csv.reader(dose1_read_obj),1,None):

            # First, add the video that goes before each scenario
            yield create_video_page(scenario_num+1)

            domain, label = row[0].strip(), row[3]
            puzzle1,puzzle2 = map(create_puzzle,row[4:6])
            question, choices, answer = row[6], row[7:9], row[7]
            image_url = media_url(row[9])

            shuffle(choices)

            yield from create_scenario_pages(domain=domain, label=label, scenario_num=scenario_num,
                                                    puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                                    comp_question=question, answers=choices,
                                                    correct_answer=answer, word_2=puzzle2[1],
                                                    puzzle_text_2=puzzle2[0], image_url=image_url,
                                                    is_first=scenario_num==0)
            scenario_num += 1

def _create_survey_page(row):
    text = clean_up_unicode(row[4])

    title = row[1].strip()
    input_1 = lower(row[5])
    input_2 = lower(row[6])
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

def domain_selection_text():
    return (
        "Los dominios enumerados aquí son algunas áreas que pueden hacerte sentir "
        "ansioso. Seleccione en qué le gustaría trabajar durante el día de hoy"
        "formación. \n\nTe animamos a elegir diferentes dominios para practicar "
        "¡Pensar con flexibilidad en todas las áreas de tu vida!"
    )

def create_lessons_learned():
    """
    A function that reads in the file that has the text for each lesson learned.

    :param file_path: file path for lessons learned text (.csv)
    :return: lessons learned dictionary, key = domain, field = lessons learned text for that domain

    https://docs.google.com/spreadsheets/d/1kM80BHglwtsBgxntJDRdfNj-cusgGGJ0sx814ctB1pk/edit#gid=0
    """
    with open(f"{dir_csv}/Spanish lessons_learned_text.csv", 'r', encoding='utf-8') as read_obj:
        return { row[0]:row[1] for row in islice(csv.reader(read_obj),1,None) }

def create_long_sessions(i):
    sessions = defaultdict(list)

    with open(f"{dir_csv}/Spanish_Long_Scenarios.csv", "r",encoding="utf-8") as read_file:
        for row in islice(csv.reader(read_file),2,None):

            if not row: continue # Skip empty lines

            if len(row) > i + 16:  # Ensure the row has enough columns
                domain_1 = row[0].strip()
                domain_2 = row[1].strip() if row[1] else None
                label = row[3]
                image_url = media_url(row[5])
                scenario_description = row[i]
                thoughts = row[i+2:i+7]
                feelings = row[i+7:i+12]
                behaviors = row[i+12:i+17]

                if not has_value(scenario_description) or not has_value(label): continue

                dose = create_long_pages(label=label, scenario_description=scenario_description,
                                          image_url=image_url,thoughts=thoughts,
                                          feelings=feelings, behaviors=behaviors)

                if domain_1: sessions[domain_1].append(dose)
                if domain_2: sessions[domain_2].append(dose)

    # shuffle each list of long scenario page groups
    for domain in sessions: shuffle(sessions[domain])

    return {k:iter(cycle(v)) for k,v in sessions.items()}

def create_short_sessions(i):
    sessions     = defaultdict(list)
    scenarios    = defaultdict(list)
    scenario_num = defaultdict(int)

    lessons_learned_dict = create_lessons_learned()

    with open(f"{dir_csv}/Spanish_Short_Scenarios.csv","r", encoding="utf-8", newline='') as read_obj:
        for row in islice(csv.reader(read_obj),1,None):

            domain    = row[0].strip()
            label     = row[4]
            image_url = media_url(row[11])
            tipe      = lower(row[3]).strip()

            if not domain or not label: continue

            is_wyo = "write your own" in lower(label)

            if len(scenarios[domain]) == 10 or is_wyo and len(scenarios[domain]) > 6:
                sessions[domain].append(sum(scenarios[domain],[]))
                scenarios[domain] = []

            if is_wyo:
                sessions[domain].append("Write Your Own")
                scenarios[domain] = []

            else:

                puzzle1,puzzle2 = map(create_puzzle,row[i:i+2])

                if puzzle1 == (None,None): continue

                comp_question, choices, answer  = row[i+2], row[i+3:i+5], row[i+3]

                if lower(choices[0]).strip() in ['yes','si','no','sí']: choices = ["Sí","No"] #changed

                shuffle(choices)

                if row[12]: letters_missing = row[12]

                is_first_session = len(sessions[domain]) == 0
                is_first_scenario = len(scenarios[domain]) == 0

                show_lessons_learned = not is_first_session and is_first_scenario and len(sessions[domain]) % 4 == 0

                scenarios[domain].append(
                    create_scenario_pages(domain=domain, label=label, scenario_num=scenario_num[domain],
                        puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                        comp_question=comp_question, answers=choices,
                        correct_answer=answer, word_2=puzzle2[1],
                        puzzle_text_2=puzzle2[0], image_url=image_url,
                        n_missing=letters_missing,
                        include_lessons_learned=show_lessons_learned,
                        lessons_learned_dict=lessons_learned_dict,
                        is_first=is_first_scenario, tipe=tipe
                    )
                )

    return sessions

def create_surveys():
    # The keys in this dictionary correspond to the HTC_survey_questions.csv lookup codes ([Subject]_[Doses])
    # You can see all the lookup codes and their meanings below:
    # https://docs.google.com/spreadsheets/d/1Z_syG-HbyFT2oqMsHnAbidRtlH97IVxnBqbNKZWbwLY/edit#gid=0
    surveys = { "BeforeDomain_All": defaultdict(list), "AfterDomain_All": defaultdict(list), "Dose_1": defaultdict(list), "Control_Dose_1": defaultdict(list) }

    # Open the file with all the content
    with open(f"{dir_csv}/MTSpanish_survey_questions.csv", "r", encoding="utf-8") as read_obj:
        for row in islice(csv.reader(read_obj),1,None):
            lookup_id = f"{row[3]}_{row[2]}"
            subgroup_id = row[0]

            if lookup_id not in surveys: continue

            elif row[0] == "Práctica CBM-I":
                surveys[lookup_id][subgroup_id].extend(_create_practice_pages())
            elif row[2]:
                surveys[lookup_id][subgroup_id].append(_create_survey_page(row))

    return surveys

def create_write_your_own_session():
    pages = []
    with open(f"{dir_csv}/Spanish_write_your_own.csv", "r", encoding="utf-8") as f:
        for row in islice(csv.reader(f),1,None):
            text = clean_up_unicode(row[4])
            if text:
                title = row[1]
                input_1 = row[5]
                input_name = row[18]
                pages.append(create_write_your_own_page(text, input_1, title, input_name))
    return pages

def create_resource_dose_creator():
    ER_lookup = get_ER(file_path=f"{dir_csv}/ER_Strategies.csv")
    tips      = get_tips(file_path=f"{dir_csv}/tips.csv")
    resources = get_resources(file_path=f"{dir_csv}/Spanish_Resources.csv")

    return lambda domain: [create_resource_page(resources, tips, ER_lookup, domain)]

def create_discrimination_session(pop):
    pages = []
    with open(f"{dir_csv}/Discrimination.csv", "r", encoding="utf-8") as f:
        for row in islice(csv.reader(f),1,None):
            title, text, input_1, var_name, input_name = row[0], row[1], row[2], row[13], row[15]
            items, conditions = row[7], row[14]
            text = f'Vaya a la libreria de recursos disponibles los enlaces a estos recursos.\n\n{clean_up_unicode(row[1])}' #changed

            pages.append(create_discrimination_page(conditions=conditions,
                                                    text=text,
                                                    items=items,
                                                    input_1=input_1,
                                                    input_name=input_name,
                                                    variable_name=var_name,
                                                    title=title))

    return pages

populations = [ ["Español", 5, 4] ]

for pop,s,l in populations:

    surveys         = create_surveys()
    short_sessions  = create_short_sessions(s)             # dict of short session iter by domain
    long_sessions   = create_long_sessions(l)              # dict of long session cycle by domain
    wyo_session     = create_write_your_own_session()      # one session used over and over again
    resources       = create_resource_dose_creator()       # lambda that takes a domain and returns a dose
    discrim_session = create_discrimination_session(pop)   # one session used over and over again

    domains  = short_sessions.keys()
    sessions = defaultdict(list)

    # Load info bubbles data
    # info_dict = {}
    # with open(f"{dir_csv}/Info_Bubbles.csv", "r", encoding="utf-8") as info_file:
    #     for row in islice(csv.reader(info_file), 1, None):
    #         timing, text = row[0], row[1]
    #         info_dict[int(timing)] = clean_up_unicode(text)

    # Create doses
    for domain in domains:
        for short_session in short_sessions[domain]:
            if sessions[domain] and len(sessions[domain]) % 5 == 0:
                sessions[domain].append(next(long_sessions[domain]) + resources(domain))
            if short_session == "Write Your Own":
                sessions[domain].append(wyo_session + resources(domain))
            else:
                sessions[domain].append(short_session + resources(domain))

    # Define folders
    folders = {}
    folders['control/sessions/__first__'] = flat(surveys["Control_Dose_1"])
    folders['treatment/sessions/__flow__.json'] = {"mode":"select", "title_case": True, "column_count":2, "text": domain_selection_text(), "title":"MindTrails Español"}
    folders['treatment/sessions/__first__'] = flat(surveys["Dose_1"])
    folders['treatment/sessions/__before__'] = flat(surveys["BeforeDomain_All"])
    folders['treatment/sessions/__after__'] = flat(surveys["AfterDomain_All"])
    folders['treatment/sessions/Discriminación'] = discrim_session
    for domain, doses in sessions.items():
        folders[f'treatment/sessions/{dir_safe(domain)}/__flow__.json'] ={"mode":"sequential", "take":1, "repeat":True}
        for i, dose in enumerate(doses,1):
            folders[f'treatment/sessions/{dir_safe(domain)}/{i}'] = dose

    # Delete old JSON
    shutil.rmtree(f"{dir_out}/control/sessions",ignore_errors=True)
    shutil.rmtree(f"{dir_out}/treatment/sessions",ignore_errors=True)

    # Write new JSON
    write_output(dir_out, folders)