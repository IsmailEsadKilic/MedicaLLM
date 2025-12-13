import xml.etree.ElementTree as ET

ns = {'db': 'http://www.drugbank.ca'}

for event, elem in ET.iterparse('drugbank_data/full database 2.xml', events=('end',)):
    if elem.tag == '{http://www.drugbank.ca}drug':
        print("📋 Available fields for a drug (Lepirudin - DB00001):\n")
        
        count = 0
        for child in elem:
            count += 1
            tag = child.tag.replace('{http://www.drugbank.ca}', '')
            if child.text and len(child.text.strip()) > 0:
                preview = child.text.strip().replace('\n', ' ')[:60]
                print(f"  • {tag}: {preview}...")
            else:
                print(f"  • {tag}: (nested/empty)")
        
        print(f"\n✅ Total fields: {count}")
        break
