
from pathlib import Path
from xsdata.formats.dataclass.parsers import XmlParser
from drugbank_schema import Drugbank 
from pympler import asizeof

DATA_DIRECTORY_PATH = "../data/xml"
# [xml]$ ls
# drugbank.xml drugbank.xsd _lepirudin.xml


def parse_drugbank_xml(filename: str = "drugbank/_lepirudin.xml") -> Drugbank:
    """
    Parses the Drugbank XML file into Python objects.
    """
    parser = XmlParser()
    file_path = Path(DATA_DIRECTORY_PATH) / filename
    
    # This magic line converts XML -> Python Objects
    drugbank_data = parser.parse(file_path, Drugbank)
    
    return drugbank_data

if __name__ == "__main__":
    # 1. Load the data
    # data = parse_drugbank_xml()
    data = parse_drugbank_xml("drugbank/drugbank.xml")
    
    print(f"Size: {asizeof.asizeof(data) / 1024 / 1024:.2f} MB")
 
