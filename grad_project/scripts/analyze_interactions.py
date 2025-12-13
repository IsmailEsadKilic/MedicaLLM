import xml.etree.ElementTree as ET
from collections import defaultdict
import json

# Parse DrugBank XML - process only first 100 drugs
context = ET.iterparse('drugbank_data/full database 2.xml', events=('start', 'end'))
context = iter(context)
event, root = next(context)

ns = {'db': 'http://www.drugbank.ca'}

interactions = []
drug_names = {}
drug_count = 0
max_drugs = 100

for event, elem in context:
    if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
        if drug_count >= max_drugs:
            break
            
        drug_id = elem.find('db:drugbank-id[@primary="true"]', ns)
        drug_name = elem.find('db:name', ns)
        
        if drug_id is not None and drug_name is not None:
            drug_names[drug_id.text] = drug_name.text
            
            drug_interactions = elem.find('db:drug-interactions', ns)
            if drug_interactions is not None:
                for interaction in drug_interactions.findall('db:drug-interaction', ns):
                    interacting_id = interaction.find('db:drugbank-id', ns)
                    interacting_name = interaction.find('db:name', ns)
                    description = interaction.find('db:description', ns)
                    
                    interactions.append({
                        'drug1_id': drug_id.text,
                        'drug1_name': drug_name.text,
                        'drug2_id': interacting_id.text if interacting_id is not None else '',
                        'drug2_name': interacting_name.text if interacting_name is not None else '',
                        'description': description.text if description is not None else ''
                    })
        
        drug_count += 1
        elem.clear()

print(f"Processed drugs: {len(drug_names)}")
print(f"Total interactions found: {len(interactions)}")

# Most interacting drugs
interaction_counts = defaultdict(int)
for i in interactions:
    interaction_counts[i['drug1_name']] += 1

top_10 = sorted(interaction_counts.items(), key=lambda x: x[1], reverse=True)[:10]
print("\nTop 10 drugs with most interactions:")
for drug, count in top_10:
    print(f"  {drug}: {count} interactions")

# Save to JSON
with open('drug_interactions.json', 'w') as f:
    json.dump(interactions, f, indent=2)

print(f"\nInteractions saved to drug_interactions.json")
