import json
from collections import Counter

with open('drug_interactions.json', 'r') as f:
    interactions = json.load(f)

print(f"=== DRUG-DRUG INTERACTION ANALYSIS ===\n")
print(f"Total interactions analyzed: {len(interactions)}\n")

# Interaction types analysis
interaction_types = []
for i in interactions:
    desc = i['description'].lower()
    if 'increase' in desc and 'risk' in desc:
        interaction_types.append('Risk Increase')
    elif 'decrease' in desc and 'effect' in desc:
        interaction_types.append('Effect Decrease')
    elif 'increase' in desc and 'effect' in desc:
        interaction_types.append('Effect Increase')
    elif 'metabolism' in desc:
        interaction_types.append('Metabolism')
    else:
        interaction_types.append('Other')

type_counts = Counter(interaction_types)
print("Interaction Types:")
for itype, count in type_counts.most_common():
    print(f"  {itype}: {count} ({count/len(interactions)*100:.1f}%)")

# Sample interactions
print("\n=== SAMPLE INTERACTIONS ===")
for i in interactions[:5]:
    print(f"\n{i['drug1_name']} + {i['drug2_name']}")
    print(f"  → {i['description']}")

print(f"\n✓ Full data available in drug_interactions.json")
