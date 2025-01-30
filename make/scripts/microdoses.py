import csv
import shutil
import json

from collections import defaultdict
from itertools import islice, cycle
from pathlib import Path

from helpers_pages import create_discrimination_page, create_scenario_pages, create_survey_page,create_resource_page, create_long_pages
from helpers_utilities import get_resources, get_ER, get_tips, clean_up_unicode, has_value, create_puzzle, dir_safe, shuffle

dir_root = "./make"
dir_csv   = f"{dir_root}/CSV"
dir_out   = f"{dir_root}/~out"
dir_flows = f"{dir_out}/treatment/flows"
dir_doses = f"{dir_flows}/doses"

Path(dir_out).mkdir(parents=True,exist_ok=True)

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

def domain_selection_text():
    return (
        "Los dominios enumerados aquí son algunas áreas que pueden hacerte sentir "
        "ansioso. Seleccione en qué le gustaría trabajar durante el día de hoy"
        "formación. \n\nTe animamos a elegir diferentes dominios para practicar "
        "¡Pensar con flexibilidad en todas las áreas de tu vida!"
    )

def create_long_doses(i):
    long_doses = defaultdict(list)

    with open(f"{dir_csv}/Spanish_Long_Scenarios.csv", "r",encoding="utf-8") as read_file:
        i = groups[group_name][1]  # 4  # changed
        for row in islice(csv.reader(read_file),2,None):

            if not row: continue # Skip empty lines

            if len(row) > max(i + 16, 3):  # Ensure the row has enough columns
                domain_1 = row[0].strip()
                domain_2 = row[1].strip() if row[1] else None
                label = row[3]
                scenario_description = row[i]
                thoughts = row[i+2:i+7]
                feelings = row[i+7:i+12]
                behaviors = row[i+12:i+17]
                unique_image = False

                if not has_value(scenario_description) or not has_value(label): continue

                dose = create_long_pages(label=label, scenario_description=scenario_description,
                                          unique_image=unique_image, thoughts=thoughts,
                                          feelings=feelings, behaviors=behaviors)
                # add page group to correct domain's list
                long_doses[domain_1].append(dose)
                # if it also belongs to a second domain, add the page group to that list
                if domain_2: long_doses[domain_2].append(dose)

    # Shuffling here doesn't really make sense anymore
    # since there is only one protocol shared by all
    # participants. Also, shuffling now makes github
    # commits show diffs where nothing really changed.
    # This isn't a problem, it just makes it a little
    # harder to make sure you didn't introduce an 
    # unintentional change.
    # ----------------------------------------------
    # shuffle each list of long scenario page groups
    # for domain in long_doses:
    #     shuffle(long_doses[domain])

    return {k:iter(cycle(v)) for k,v in long_doses.items()}

def create_short_doses(i):
    short_doses   = defaultdict(list)
    domain_rindex = defaultdict(int)
    domain_ndoses = defaultdict(int)

    unique_image = False

    with open(f"{dir_csv}/Spanish_Short_Scenarios.csv","r", encoding="utf-8", newline='') as read_obj:

        for row in islice(csv.reader(read_obj),1,None):
            domain_1 = row[0].strip() #Broad domain 1
            label    = row[3]  # scenario name, Hoos TC title column

            if not domain_1 or not label: continue

            if "Write Your Own" in label:
                # Add a place holder that will be replaced with
                # a write your own dose in final processing
                short_doses[domain_1].append("Write Your Own")
                domain_ndoses[domain_1] += 10 #bump the dose count by 10 (because the dose size of a long scenario = 10)
                continue

            domain_rindex[domain_1] += 1
            domain_ndoses[domain_1] += 1

            puzzle1,puzzle2 = map(create_puzzle,row[i:i+2])

            comp_question, choices, answer  = row[i+2], row[i+3:i+5], row[i+3]

            if choices[0].strip().lower() in ['yes','si','no','sí']: choices = ["Sí","No"] #changed

            shuffle(choices)

            if row[10]: letters_missing = row[10]

            # Every 40 doses we want to show them lessons learned.
            # This doesn't account for long scenarios or write your own
            lessons_learned = domain_ndoses[domain_1] % 40 == 0

            dose = create_scenario_pages(domain=domain_1, label=label, scenario_num=domain_rindex[domain_1],
                                         puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                         comp_question=comp_question, answers=choices,
                                         correct_answer=answer, word_2=puzzle2[1],
                                         puzzle_text_2=puzzle2[0],
                                         letters_missing=letters_missing,
                                         lessons_learned=lessons_learned,
                                         unique_image=unique_image,
                                         row_num=domain_ndoses[domain_1])

            short_doses[domain_1].append(dose)

    return short_doses

def create_surveys():
    # The keys in this dictionary correspond to the HTC_survey_questions.csv lookup codes ([Subject]_[Doses])
    # You can see all the lookup codes and their meanings below:
    # https://docs.google.com/spreadsheets/d/1Z_syG-HbyFT2oqMsHnAbidRtlH97IVxnBqbNKZWbwLY/edit#gid=0
    surveys = { "BeforeDomain_All": defaultdict(list), "AfterDomain_All": defaultdict(list) }

    # Open the file with all the content
    with open(f"{dir_csv}/MTSpanish_survey_questions.csv", "r", encoding="utf-8") as read_obj:
        for row in islice(csv.reader(read_obj),1,None):
            lookup_id = f"{row[3]}_{row[2]}"
            subgroup_id = row[0]
            if lookup_id not in surveys: continue
            if row[2]: surveys[lookup_id][subgroup_id].append(_create_survey_page(row))
    return surveys

def create_write_your_own_dose():
    pages = []
    with open(f"{dir_csv}/Spanish_write_your_own.csv", "r", encoding="utf-8") as f:
        for row in islice(csv.reader(f),1,None):
            text = clean_up_unicode(row[4])
            if text:
                title = row[1]
                input_1 = row[5]
                input_name = row[18]
                page = create_survey_page(text=text, input_1=input_1, title=title, input_name=input_name)
                page["name"] = "Write Your Own"
                page["title"] = title or "Escribe El tuyo"
                pages.append(page)
    return pages

def create_resource_dose_creator():
    ER_lookup = get_ER(file_path=f"{dir_csv}/ER_Strategies.csv")
    tips      = get_tips(file_path=f"{dir_csv}/tips.csv")
    resources = get_resources(file_path=f"{dir_csv}/Spanish_Resources.csv")

    return lambda domain: [create_resource_page(resources, tips, ER_lookup, domain)]

def create_discrimination_dose(group_name):
    pages = []
    with open(f"{dir_csv}/Discrimination.csv", "r", encoding="utf-8") as f:
        for row in islice(csv.reader(f),1,None):
            title, input_1, participant_group, input_name = row[0], row[2], row[3], row[15]
            items, conditions = clean_up_unicode(row[7]).split("; "), row[14].split('; ')
            text = f'Vaya a la libreria de recursos disponibles los enlaces a estos recursos.\n\n{clean_up_unicode(row[1])}' #changed

            if group_name not in participant_group: continue  # checking if it corresponds to the group we're dealing with

            pages.append(create_discrimination_page(conditions=conditions,
                                                    text=text,
                                                    items=items,
                                                    input_1=input_1,
                                                    input_name=input_name,
                                                    title=title))

            return pages

groups = { "Español": [4, 4] }

for group_name, group in groups.items():

    surveys      = create_surveys()
    short_doses  = create_short_doses(group[0])             # dict of doses by domain
    long_doses   = create_long_doses(group[1])              # dict of dose cycle by domain
    wyo_dose     = create_write_your_own_dose()             # one dose used over and over again
    resources    = create_resource_dose_creator()           # lambda that takes a domain and returns a dose
    discrim_dose = create_discrimination_dose(group_name)   # one dose used over and over again

    domains      = short_doses.keys()
    domain_doses = defaultdict(list)
    domain_doses["Discrimination"].append(discrim_dose)

    # Read dose content
    for domain in domains:
        dose_count = 0
        for short_dose in short_doses[domain]:

            if short_dose == "Write Your Own":
                dose_count += 10 #bump the row by 10 (because the dose size of a long scenario = 10)
                domain_doses[domain].append(wyo_dose)
                domain_doses[domain].append(resources(domain))
                continue

            domain_doses[domain].append(short_dose)

            if dose_count % 10 == 0:
                domain_doses[domain].append(resources(domain))

            if dose_count % 50 == 0:
                long_dose = next(long_doses[domain])
                domain_doses[domain].append(resources(domain))

            dose_count += 1

    shutil.rmtree(dir_doses,ignore_errors=True)

    # Write the dose files
    for domain, doses in domain_doses.items():
        dir_domain = f"{dir_doses}/{dir_safe(domain)}"
        Path(dir_domain).mkdir(parents=True)

        for i,dose in enumerate(doses,1):
            dir_dose = f"{dir_domain}/{i}"
            Path(dir_dose).mkdir(parents=True)

            for j,page in enumerate(dose,1):
                with open(f"{dir_dose}/{j}.json", 'w+', encoding='utf-8') as outfile:
                    json.dump(page, outfile, indent=4, ensure_ascii=False)

    #Configure dose selection
    with open(f"{dir_doses}/__flow__.json", 'w+', encoding='utf-8') as outfile:
        json.dump({"mode":"select", "text":domain_selection_text(), "title":"MindTrails Español"}, outfile, indent=4, ensure_ascii=False)

    for domain, doses in domain_doses.items():
        dir_domain = f"{dir_doses}/{dir_safe(domain)}"
        with open(f"{dir_domain}/__flow__.json", 'w+', encoding='utf-8') as outfile:
            json.dump({"mode":"sequential", "size":1, "repeat":True}, outfile, indent=4, ensure_ascii=False)
