import xml.etree.ElementTree as ET
import json

ns = {'db': 'http://www.drugbank.ca'}

context = ET.iterparse('drugbank_data/full database 2.xml', events=('start', 'end'))
context = iter(context)
event, root = next(context)

current_drug = {}
in_drug = False
current_path = []

for event, elem in context:
    if event == 'start':
        current_path.append(elem.tag)
    elif event == 'end':
        if elem.tag == '{http://www.drugbank.ca}drug':
            if current_drug:
                print(f"🔍 Drug: {current_drug.get('name', 'Unknown')} ({current_drug.get('drug_id', 'N/A')})\n")
                print(json.dumps(current_drug, indent=2, ensure_ascii=False))
                break
            elem.clear()
        elif len(current_path) >= 2 and current_path[-2] == '{http://www.drugbank.ca}drug':
            tag = elem.tag.replace('{http://www.drugbank.ca}', '')
            
            if tag == 'drugbank-id' and elem.get('primary') == 'true':
                current_drug['drug_id'] = elem.text
            elif tag in ['name', 'description', 'cas-number', 'unii', 'state', 'indication', 
                        'pharmacodynamics', 'mechanism-of-action', 'toxicity', 'metabolism',
                        'absorption', 'half-life', 'protein-binding', 'route-of-elimination']:
                if elem.text:
                    current_drug[tag.replace('-', '_')] = elem.text[:200] if len(elem.text) > 200 else elem.text
            elif tag == 'groups':
                current_drug['groups'] = [g.text for g in elem.findall('db:group', ns) if g.text]
            elif tag == 'synonyms':
                current_drug['synonyms'] = [s.text for s in elem.findall('db:synonym', ns) if s.text][:5]
            elif tag == 'categories':
                current_drug['categories'] = [c.text for c in elem.findall('.//db:category', ns) if c.text][:5]
        
        current_path.pop()
