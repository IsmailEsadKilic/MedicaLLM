import xml.etree.ElementTree as ET

ns = {'db': 'http://www.drugbank.ca'}

count = 0
for event, elem in ET.iterparse('drugbank_data/full database 2.xml', events=('end',)):
    if elem.tag == '{http://www.drugbank.ca}drug' and count < 5:
        name = elem.find('db:name', ns)
        synonyms_elem = elem.find('db:synonyms', ns)
        
        if name is not None and synonyms_elem is not None:
            synonyms = [s.text for s in synonyms_elem.findall('db:synonym', ns) if s.text]
            print(f"\n🔍 {name.text}")
            print(f"   Synonyms ({len(synonyms)}): {synonyms[:5]}")
            count += 1
        
        elem.clear()
        if count >= 5:
            break
