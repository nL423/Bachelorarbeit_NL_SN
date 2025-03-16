import requests
import pandas as pd
import os
import urllib.parse


class Helper:
    def __init__(self, csv_path='../newapp/ressources/mintMap.csv'):
        """
        Initializes the Helper
        """
        self.csv_path = csv_path
        self.mint_query = """
            PREFIX rdf:	<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX bio:	<http://purl.org/vocab/bio/0.1/>
            PREFIX crm:	<http://www.cidoc-crm.org/cidoc-crm/>
            PREFIX dcmitype:	<http://purl.org/dc/dcmitype/>
            PREFIX dcterms:	<http://purl.org/dc/terms/>
            PREFIX foaf:	<http://xmlns.com/foaf/0.1/>
            PREFIX geo:	<http://www.w3.org/2003/01/geo/wgs84_pos#>
            PREFIX nm:	<http://nomisma.org/id/>
            PREFIX nmo:	<http://nomisma.org/ontology#>
            PREFIX org:	<http://www.w3.org/ns/org#>
            PREFIX osgeo:	<http://data.ordnancesurvey.co.uk/ontology/geometry/>
            PREFIX rdac:	<http://www.rdaregistry.info/Elements/c/>
            PREFIX skos:	<http://www.w3.org/2004/02/skos/core#>
            PREFIX spatial: <http://jena.apache.org/spatial#>
            PREFIX un:	<http://www.owl-ontologies.com/Ontology1181490123.owl#>
            PREFIX wordnet: <http://ontologi.es/WordNet/class/>
            PREFIX xsd:	<http://www.w3.org/2001/XMLSchema#>

            SELECT distinct ?mint ?mintLabel WHERE {
                ?coinType nmo:hasMint ?mintPlace .
                ?coinType rdf:type nmo:TypeSeriesItem.
                ?coinType nmo:hasMint ?mint . 
                ?mint skos:prefLabel ?mintLabel FILTER(langMatches(lang(?mintLabel), "en"))
            }
        """

        self.downloadMintMapFromNomisma()

    def downloadMintMapFromNomisma(self):
        """
        Downloads the mint map CSV from the Nomisma SPARQL endpoint and saves it to the specified path.
        """
        print("Downloading MintMap file from Nomisma... (This may take a while)")

        encoded_query = urllib.parse.quote(self.mint_query)
        url = f"http://nomisma.org/query?query={encoded_query}&output=csv"

        response = requests.get(url)
        
        if response.status_code == 200:
            with open(self.csv_path, 'wb') as file:
                file.write(response.content)
            print("MintMap file downloaded and saved successfully.")
        else:
            print(f"Failed to download the MintMap file, status code: {response.status_code}")
    
    def get_mint_map(self):
        """
        Loads the mint map from the saved CSV file and converts it to a dictionary.

        Returns:
        dict: A dictionary mapping mint IDs to mint labels.
        """
        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            df = df.set_index('mint')
            mint_map = df['mintLabel'].to_dict()
            return mint_map
        else:
            print("MintMap csv file does not exist.")
            return {}