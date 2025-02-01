import shutil
import csv
import json

from itertools import islice
from collections import defaultdict
from pathlib import Path

from helpers_utilities import dir_safe, get_groupnames
from helpers_pages import create_subdomain_page

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

#elements
def resource_text(resource_name, resource_link, resource_text):
    return f"""<b><font color="#9769ED" size=6>{resource_name}</font></b>
               <br/><br/>{resource_text}<br/><br/>
               <a href="{resource_link}">{resource_link}</a>"""

domains = defaultdict(lambda:defaultdict(list))

# Read the resource data
with open(f"{dir_csv}/MTSpanish_on-demand.csv", "r", encoding="utf-8") as read_obj:
    for row in islice(csv.reader(read_obj), 2, None):
        domain,subdomain,res_name,res_link,res_text = row
        domains[domain][subdomain].append(resource_text(res_name,res_link,res_text))

for groupname in get_groupnames():

    shutil.rmtree(f"{dir_out}/{groupname}/resources",ignore_errors=True)

    # Write resource Pages
    for domain, subdomains in domains.items():
        dir_dom = f"{dir_out}/{groupname}/resources/{dir_safe(domain)}"
        Path(dir_dom).mkdir(parents=True)
        for subdomain, resources in subdomains.items():
            with open(f"{dir_dom}/{dir_safe(subdomain)}.json", 'w+', encoding='utf-8') as outfile:
                json.dump(create_subdomain_page(subdomain, resources), outfile, indent=4, ensure_ascii=False)

    # Configure Flow Guides
    with open(f"{dir_out}/{groupname}/resources/__flow__.json", 'w+', encoding='utf-8') as outfile:
        json.dump({"mode":"select"}, outfile, indent=4, ensure_ascii=False)

    for domain, subdomains in domains.items():
        with open(f"{dir_out}/{groupname}/resources/{dir_safe(domain)}/__flow__.json", 'w+', encoding='utf-8') as outfile:
            json.dump({"mode":"select"}, outfile, indent=4, ensure_ascii=False)
