import shutil
import csv
import json

from itertools import islice
from collections import defaultdict
from pathlib import Path

from helpers_utilities import dir_safe, get_groupnames

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def subdomain_step(domain,subdomain):
    return {
        "path":f"page://scripts/pages/{dir_safe(domain)}/{dir_safe(subdomain)}/1.json",
        "conditions": [ {"variable":"action", "comparator":"=" , "value": dir_safe(subdomain) } ]
    }

#elements
def resource_text(resource_name, resource_link, resource_text):
    return f"""<b><font color="#9769ED" size=6>{resource_name}</font></b>
               <br/><br/>{resource_text}<br/><br/>
               <a href="{resource_link}">{resource_link}</a>"""

def domain_button(domain):
    return {
        "text": domain,
        "action": f"flow://scripts/flows/resources-{dir_safe(domain)}.json"
    }

def subdomain_button(subdomain):
    return { "type": "Button", "text": subdomain, "action": dir_safe(subdomain) }

#pages
def subdomain_pick_page(domain, subdomains):
    subdomain_picker_text = { "type": "Text", "text": "Haga clic en el tema específico para ver los recursos asociados." }
    subdomain_picker_buttons = map(subdomain_button,subdomains)
    return {
        "name": "Which subdomain?",
        "title": domain,
        "elements": [ subdomain_picker_text, *subdomain_picker_buttons ]
    }

def subdomain_text_page(subdomain, resource_texts):
    resource_text = '<br/><br/><br/><br/>'.join(resource_texts)
    return {
        "name": subdomain,
        "title": subdomain,
        "elements": [ { "type": "Text", "html": True, "text": resource_text } ]
    }

domains = defaultdict(lambda:defaultdict(list))

# Read the resource data
with open(f"{dir_csv}/MTSpanish_on-demand.csv", "r", encoding="utf-8") as read_obj:
    for row in islice(csv.reader(read_obj), 2, None):
        domain,subdomain,res_name,res_link,res_text = row
        domains[domain][subdomain].append(resource_text(res_name,res_link,res_text))

for groupname in get_groupnames():

    shutil.rmtree(f"{dir_out}/{groupname}/flows/resources",ignore_errors=True)

    # Write resource files
    for domain, subdomains in domains.items():
        dir_dom = f"{dir_out}/{groupname}/flows/resources/{dir_safe(domain)}"

        Path(dir_dom).mkdir(parents=True)

        for subdomain, resources in subdomains.items():
            with open(f"{dir_dom}/{dir_safe(subdomain)}.json", 'w+', encoding='utf-8') as outfile:
                json.dump(subdomain_text_page(subdomain, resources), outfile, indent=4, ensure_ascii=False)

    # Configure how they run
    with open(f"{dir_out}/{groupname}/flows/resources/__flow__.json", 'w+', encoding='utf-8') as outfile:
        json.dump({"mode":"select"}, outfile, indent=4, ensure_ascii=False)

    for domain, subdomains in domains.items():
        with open(f"{dir_out}/{groupname}/flows/resources/{dir_safe(domain)}/__flow__.json", 'w+', encoding='utf-8') as outfile:
            json.dump({"mode":"select"}, outfile, indent=4, ensure_ascii=False)
