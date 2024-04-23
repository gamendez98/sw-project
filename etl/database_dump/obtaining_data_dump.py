from neo4j import GraphDatabase
from neo4j_backup import Extractor

if __name__ == "__main__":
    uri = "neo4j://localhost:7687"
    username = "neo4j"
    password = "neo4j"
    encrypted = False
    trust = "TRUST_ALL_CERTIFICATES"
    driver = GraphDatabase.driver(uri, auth=(username, password), encrypted=encrypted, trust=trust)

    database = "neo4j"

    project_dir = "data_dump"
    input_yes = False
    compress = True
    indent_size = 4
    json_file_size: int = int("0xFFFF", 16)
    extractor = Extractor(project_dir=project_dir, driver=driver, database=database,
                          input_yes=input_yes, compress=compress, indent_size=indent_size,
                          pull_uniqueness_constraints=True)
    extractor.extract_data()