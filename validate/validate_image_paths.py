from pathlib import Path
import json

def validate_file(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k.lower() in ['url','file'] and not Path(f'./src/{v}').exists():
                yield v
            else:
                yield from validate_file(v)
    if isinstance(obj,list):
        for o in obj:
            yield from validate_file(o)

def validate_dir(dir):
    for p in Path(dir).iterdir():

        if(p.is_dir()):
            validate_dir(p)
            continue

        with open(p, encoding='utf-8') as f:
            
            bad_links = list(validate_file(json.load(f)))

            if bad_links:
                print(p)
                for l in bad_links:
                    print(f'  {l}')

validate_dir('./src/flows')