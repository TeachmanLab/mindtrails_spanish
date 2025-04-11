import shutil
import csv

from itertools import islice
from collections import defaultdict
from pathlib import Path

from helpers_pages import create_subdomain_page
from helpers_utilities import dir_safe, get_groupnames, write_output

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def resource_domain_selection_text():
    return ("Haga clic en cualquier tema para conocer "
            "los recursos que pueden ayudarle a gestionar "
            "esa. Parte de tu vida.")

def resource_subdomain_selection_text():
    return ("Haga clic en el tema específico para ver los "
            "recursos asociados.")

def resource_text(resource_name, resource_link, resource_text):
    return f"""<b><font color="#9769ED" size=6>{resource_name}</font></b>
               <br/><br/>{resource_text}<br/><br/>
               <a href="{resource_link}">{resource_link}</a>"""

domains = defaultdict(lambda: defaultdict(list))

# Read the resources
with open(f"{dir_csv}/MTSpanish_on-demand.csv", "r", encoding="utf-8") as read_obj:
    for row in islice(csv.reader(read_obj), 2, None):
        domain,subdomain,res_name,res_link,res_text = row
        domains[domain][subdomain].append(resource_text(res_name,res_link,res_text))

# Define folders
folders = {'__flow__.json': {"mode":"select", "title_case": True, "column_count": 2, "text":resource_domain_selection_text()}}
for domain, subdomains in domains.items():
    folders[f"{dir_safe(domain)}/__flow__.json"] = {"mode":"select", "text":resource_subdomain_selection_text(), "last_item": "Otro"}
    for subdomain, resources in subdomains.items():
        folders[f"{dir_safe(domain)}/{dir_safe(subdomain)}.json"] = create_subdomain_page(subdomain,resources)

# Delete old JSON
for groupname in get_groupnames():
    shutil.rmtree(f"{dir_out}/{groupname}/resources", ignore_errors=True)

# Write new JSON
for groupname in get_groupnames():
    write_output(f"{dir_out}/{groupname}/resources", folders)
