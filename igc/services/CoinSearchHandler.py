from rdflib import Graph
from rdflib.plugins.stores import sparqlstore
import re

class CoinSearchHandler():
    """
    A handler class for executing SPARQL queries against a specified RDF dataset 
    to search for numismatic objects (coins) based on various criteria.

    Attributes:
        endpoint (str): SPARQL endpoint URL.
        store (SPARQLStore): The SPARQL store connected to the endpoint.
        g (Graph): RDFLib Graph connected to the SPARQL store.
        _query_head (str): Common prefixes and initial part of the SPARQL query.
    
    Author: ??? , UPDATE by Nico Lambert
    """

    def __init__(self):
        """
        Initializes the CoinSearchHandler with a specific SPARQL endpoint.

        Author: Danilo Pantic
        """
        
        #----------------------------------------------------------- (START) UPDATE by Nico Lambert and Steven Nowak ------------------------------------------------------------
        # Temporarily adjusted endpoint to local fuseki endpoint until the parser is installed at corpus nummorum
        # When the parser is installed, change "http://localhost:3030/db_cn/sparql" to "https://data.corpus-nummorum.eu/sparql"
        self.endpoint = "http://localhost:3030/db_cn/sparql"
        #------------------------------------------------------------- (END) UPDATE by Nico Lambert and Steven Nowak ------------------------------------------------------------
        
        self.store = sparqlstore.SPARQLStore(self.endpoint)
        self.g = Graph(self.store)
        self._query_head = """
        PREFIX nmo: <http://nomisma.org/ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        """

    def executeQuery(self, query):
        """
        Executes a SPARQL query against the configured endpoint and returns the results.
        
        Parameters:
            query (str): The SPARQL query to be executed.

        Returns:
            list: A list of results obtained from the query execution.
        
        Author: Danilo Pantic
        """
        return self.g.query(query)
    
    def generateCoinQuery(self, id, coin, searchType, isNegated=False):
        """
        Generates a SPARQL query part for a specific coin based on its attributes.
        
        Parameters:
            id (str): The identifier of the coin.
            coin (dict): A dictionary containing attributes of the coin to construct the query part.
            searchType (str): The type of search to be performed.
            isNegated (bool): A flag indicating whether the query part should be negated.

        Returns:
            str: A SPARQL query part specific to the provided coin attributes.
        
        Author: Mohammed Sayed Mahmod , UPDATE by Nico Lambert
        """
        obverse_part = ""
        reverse_part = ""

        id_part = "?url dcterms:identifier ?id ."

        design_part = """OPTIONAL {
            ?url nmo:hasObverse ?obverse .
            ?obverse nmo:hasIconography ?obverseIconography .
        }"""

        thumbnail_obverse_part = """OPTIONAL {
            ?url nmo:hasObverse ?obverseSide .
            ?obverseSide foaf:thumbnail ?thumbnailObverse .
        }"""

        thumbnail_reverse_part = """OPTIONAL {
            ?url nmo:hasReverse ?reverseSide .
            ?reverseSide foaf:thumbnail ?thumbnailReverse .
        }"""

        description_obverse_part = """OPTIONAL {
            ?url nmo:hasObverse ?obverseSide .
            ?obverseSide dcterms:description ?descriptionObverse .
            FILTER (lang(?descriptionObverse) = "en")
        }"""

        description_reverse_part = """OPTIONAL {
            ?url nmo:hasReverse ?reverseSide .
            ?reverseSide dcterms:description ?descriptionReverse .
            FILTER (lang(?descriptionReverse) = "en")
        }"""

        weight_part = "OPTIONAL { ?url nmo:hasWeight ?weight . }"
        location_part = "OPTIONAL { ?url nmo:hasMint ?mint . }"
        date_part = "OPTIONAL { ?url nmo:hasDate ?date . FILTER (lang(?date) = 'en') }"
        max_diameter_part = "OPTIONAL { ?url nmo:hasMaxDiameter ?maxDiameter . }"

        
        #----------------------------------------------------------- (START) UPDATE by Nico Lambert -----------------------------------------------------------------------------
        # I changed the function "_extract_spo" to "_extract_spo_sc_oc" to extract next to subject, predicate and obj also the categories of subject and obj, because these are 
        # necessary to seperate in the "_create_sparql_part" function between a "normal" subject/obj or a "class of" subjects/objects
        # -> so i added here also the variables obverse_subject_category, obverse_object_category, reverse_subject_category and reverse_object_category
        if coin["obverse"]["coin"]:
            obverse_subject, obverse_subject_category, obverse_predicate, obverse_object, obverse_object_category = self._extract_spo_sc_oc(coin["obverse"]["coin"])
            
            obverse_part = self._create_sparql_part(id, "obverse", obverse_subject, obverse_subject_category, obverse_predicate, obverse_object, obverse_object_category, isNegated)

        if coin["reverse"]["coin"]:
            reverse_subject, reverse_subject_category, reverse_predicate, reverse_object, reverse_object_category = self._extract_spo_sc_oc(coin["reverse"]["coin"])
            reverse_part = self._create_sparql_part(id, "reverse", reverse_subject, reverse_subject_category, reverse_predicate, reverse_object, reverse_object_category, isNegated)
        #------------------------------------------------------------- (END) UPDATE by Nico Lambert -----------------------------------------------------------------------------
        

        type_part = "OPTIONAL { ?url nmo:hasTypeSeriesItem ?type . }"

        keywords_part = ""

        for kw in coin["obverse"]["keywords"]:
            if kw["negated"]:
                keywords_part += f"FILTER NOT EXISTS {{ ?obverseIconography dcterms:description ?obvDesc . FILTER regex(?obvDesc, \"{kw['text']}\", \"i\") }}\n"
            else:
                keywords_part += f"?obverseIconography dcterms:description ?obvDesc . FILTER regex(?obvDesc, \"{kw['text']}\")\n"

        for kw in coin["reverse"]["keywords"]:
            if kw["negated"]:
                keywords_part += f"FILTER NOT EXISTS {{ ?reverseIconography dcterms:description ?revDesc . FILTER regex(?revDesc, \"{kw['text']}\", \"i\") }}\n"
            else:
                keywords_part += f"?reverseIconography dcterms:description ?revDesc . FILTER regex(?revDesc, \"{kw['text']}\")\n"

        if searchType == "TypeSeriesItem":
            thumbnail_obverse_part = """
            {
            SELECT ?url (SAMPLE(?obvThumbnail) AS ?thumbnailObverse) (SAMPLE(?revThumbnail) AS ?thumbnailReverse) WHERE {
                ?numismaticObject nmo:hasTypeSeriesItem ?url ;
                                rdf:type nmo:NumismaticObject .
                OPTIONAL {
                    ?numismaticObject nmo:hasObverse ?obvSide .
                    ?obvSide dcterms:relation ?obverseRelation .
                    ?obverseRelation foaf:thumbnail ?obvThumbnail .
                }
                OPTIONAL {
                    ?numismaticObject nmo:hasObverse ?obvSide .
                    ?obvSide foaf:thumbnail ?obvThumbnail .
                }
                OPTIONAL {
                    ?numismaticObject nmo:hasReverse ?revSide .
                    ?revSide dcterms:relation ?reverseRelation .
                    ?reverseRelation foaf:thumbnail ?revThumbnail .
                }
                OPTIONAL {
                    ?numismaticObject nmo:hasReverse ?revSide .
                    ?revSide foaf:thumbnail ?revThumbnail .
                }
            } GROUP BY ?url
            }"""

            thumbnail_reverse_part = ""
        else:
            thumbnail_obverse_part = """
            OPTIONAL {
                ?url nmo:hasObverse ?obverseSide .
                ?obverseSide dcterms:relation ?obverseRelation .
                ?obverseRelation foaf:thumbnail ?thumbnailObverse .
            }
            OPTIONAL {
                ?url nmo:hasObverse ?obverseSide .
                ?obverseSide foaf:thumbnail ?thumbnailObverse .
            }
            """

            thumbnail_reverse_part = """
            OPTIONAL {
                ?url nmo:hasReverse ?reverseSide .
                ?reverseSide dcterms:relation ?reverseRelation .
                ?reverseRelation foaf:thumbnail ?thumbnailReverse .
            }
            OPTIONAL {
                ?url nmo:hasReverse ?reverseSide .
                ?reverseSide foaf:thumbnail ?thumbnailReverse .
            }
            """


        query = f"""
        {{
        ?url rdf:type nmo:{searchType} .
        {id_part}
        {design_part}
        {location_part}
        {obverse_part}
        {reverse_part}
        {thumbnail_obverse_part}
        {thumbnail_reverse_part}
        {description_obverse_part}
        {description_reverse_part}
        {weight_part}
        {date_part}
        {max_diameter_part}
        {type_part}
        {keywords_part}
        }}
        """
        return query

    def _extract_spo_sc_oc(self, coin_side):
        """
        Extracts subject, predicate, and object from a coin side specification.
        After update (from Nico Lambert) it also extracts the categories of subject and object

        Parameters:
            coin_side (dict): A dictionary representing one side of a coin.

        Returns:
            (Before Update) tuple: A tuple containing the subject, predicate, and object extracted from the coin side.
            (After Update) tuple: A tuple containing the subject, the category of the subject, predicate, object an the category of the object extracted from the coin side.
        
        Author: Danilo Pantic , UPDATE by Nico Lambert

        """
        subject = None
        subject_category = None
        predicate = None
        obj = None
        obj_category = None 

        for item in coin_side:
            
            #----------------------------------------------------------- (START) UPDATE by Nico Lambert ----------------------------------------------------------------------------- 
            # - Added extract of item category
            # - Changed extract of subject, predicate and object -> now by item["type"]
            if item["type"] == "Subj":
                subject = item["item"]["link"]
                subject_category = item["category"] 
            elif item["type"] == "Predicate":
                 predicate = item["item"]["link"]
            else:
                obj = item["item"]["link"]
                obj_category = item["category"] 
            #------------------------------------------------------------- (END) UPDATE by Nico Lambert -----------------------------------------------------------------------------
               
        return subject, subject_category, predicate, obj, obj_category # UPDATE by Nico Lambert: added extraxt of item category
    


    def _create_sparql_part(self, id, side, subject, subject_category, predicate, obj, object_category, isNegated):
        """
        Creates a SPARQL query part for a specific side of a coin based on subject, predicate, and object.
        
        Parameters:
            id (str): The identifier of the coin.
            side (str): The side of the coin ('obverse' or 'reverse').
            subject (str): The subject URI.
            subject_category (str): The category of the subject (added per update by Nico Lambert)
            predicate (str): The predicate URI.
            obj (str): The object URI.
            obj_category (str): The category of the object (added per update by Nico Lambert)
            isNegated (bool): A flag indicating whether the query part should be negated.

        Returns:
            str: A SPARQL query part for the specified side of the coin.

        Author: Danilo Pantic , UPDATE by Nico Lambert, UPDATE by Steven Nowak
        """

        #----------------------------------------------------------- (START) UPDATE by Steven Nowak -----------------------------------------------------------------------------
        # (subject and not (predicate or obj) means single word search 
        # -> instead of search in nmo:hasIconography (?{side}DesignIconography) search in nmo:hasAppearance (?{side}DesignAppearance)
        if(subject and not (predicate or obj)):
            sparql_part = f"""
            ?url nmo:has{side.capitalize()} ?{side}Side .
            ?{side}Side nmo:hasIconography ?{side}Iconography .
            ?{side}Iconography nmo:hasAppearance ?{side}DesignAppearance .
            """
            if (isNegated):
                sparql_part += f"""
                FILTER NOT EXISTS {{
                ?{side}Iconography nmo:hasAppearance ?{side}DesignAppearance2 .
                """

                #----------------------------------------------------------- (START) UPDATE by Steven Nowak (based on code from Nico Lambert) ----------------------------------------
                # if the category of the subject is "list_class" it means, the subject uri is of a class and so the instances of the class need to be filtered
                # (example: input = Deities -> we want search for instances of Deities like Artemis, Athena, etc.)
                # for this case rdf:type is used
                if subject_category == "list_class":
                    if subject:
                        sparql_part += f"?{side}DesignAppearance2 rdf:li ?instancesOfSubjectClass2 .\n"
                        sparql_part += f"?instancesOfSubjectClass2 rdf:type <{subject}> .\n"
                #----------------------------------------------------------- (-END-) UPDATE by Steven Nowak (based on code from Nico Lambert) ----------------------------------------
                else:
                    if subject:
                        sparql_part += f"?{side}DesignAppearance2 rdf:li <{subject}> .\n"

                sparql_part += "}"
            else:
                #----------------------------------------------------------- (START) UPDATE by Steven Nowak (based on code from Nico Lambert) ----------------------------------------
                # if the category of the subject is "list_class" it means, the subject uri is of a class and so the instances of the class need to be filtered
                # (example: input = Object -> we want search for instances of Object like Bow etc.)
                # for this case rdf:type is used
                if subject_category == "list_class":
                    if subject:
                        sparql_part += f"?{side}DesignAppearance rdf:li ?instancesOfSubjectClass .\n"
                        sparql_part += f"?instancesOfSubjectClass rdf:type <{subject}> .\n"
                #----------------------------------------------------------- (-END-) UPDATE by Steven Nowak (based on code from Nico Lambert) ----------------------------------------
                else:
                    if subject:
                        sparql_part += f"?{side}DesignAppearance rdf:li <{subject}> .\n"

        #----------------------------------------------------------- (-END-) UPDATE by Steven Nowak -----------------------------------------------------------------------------
        #----------------------------------------------------------- (START) UPDATE by Nico Lambert -----------------------------------------------------------------------------
        # update of triple search - now you can search after groups in the triple like "Deities holding Bow", before you were only able to search for sth. like "Artemis holding Bow"
        # -> for this, check if subject / object is a class -> class means we need to search after coins which contains at least one instance of the class on the coin image on the
        #    specific side
        else:
            sparql_part = f"""
            ?url nmo:has{side.capitalize()} ?{side}Side .
            ?{side}Side nmo:hasIconography ?{side}Iconography .
            ?{side}Iconography nmo:hasIconography ?{side}DesignIconography .
            ?{side}DesignIconography rdf:type rdf:Bag .
            ?{side}DesignIconography rdf:li ?{side}Description{id} .
            """

            if (isNegated):
                sparql_part += f"""
                FILTER NOT EXISTS {{
                ?{side}DesignIconography rdf:li ?{side}Description{id}2 .
                """
                
                #----------------------------------------------------------- (START) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                # if the category of the subject is "list_class" it means, the subject uri is of a class and so the instances of the class need to be filtered
                # (example: input = Deities -> we want search for instances of Deities like Artemis, Athena, etc.)
                # for this case rdf:type is used
                if subject_category == "list_class":
                    if subject:
                        sparql_part += f"?{side}Description{id}2 rdf:subject ?instancesOfSubjectClass2 .\n"
                        sparql_part += f"?instancesOfSubjectClass2 rdf:type <{subject}> .\n"
                #------------------------------------------------------------- (END) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                else:
                    if subject:
                        sparql_part += f"?{side}Description{id}2 rdf:subject <{subject}> .\n"
                if predicate:
                    sparql_part += f"?{side}Description{id}2 rdf:predicate <{predicate}> .\n"

                #----------------------------------------------------------- (START) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                # if the category of the object is "list_class" it means, the object uri is of a class and so the instances of the class need to be filtered
                # (example: input = Object -> we want search for instances of Object like Bow etc.)
                # for this case rdf:type is used
                if object_category == "list_class":
                    if obj:
                        sparql_part += f"?{side}Description{id}2 rdf:object ?instancesOfObjectClass2 .\n"
                        sparql_part += f"?instancesOfObjectClass2 rdf:type <{obj}> .\n"
                #------------------------------------------------------------- (END) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                else:
                    if obj:
                        sparql_part += f"?{side}Description{id}2 rdf:object <{obj}> .\n"

                sparql_part += "}"
            else:
                #----------------------------------------------------------- (START) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                # if the category of the subject is "list_class" it means, the subject uri is of a class and so the instances of the class need to be filtered
                # (example: input = Deities -> we want search for instances of Deities like Artemis, Athena, etc.)
                # for this case rdf:type is used
                if subject_category == "list_class":
                    if subject:
                        sparql_part += f"?{side}Description{id} rdf:subject ?instancesOfSubjectClass .\n"
                        sparql_part += f"?instancesOfSubjectClass rdf:type <{subject}> .\n"
                #------------------------------------------------------------- (END) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                else:
                    if subject:
                        sparql_part += f"?{side}Description{id} rdf:subject <{subject}> .\n"
                if predicate:
                    sparql_part += f"?{side}Description{id} rdf:predicate <{predicate}> .\n"

                #----------------------------------------------------------- (START) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                # if the category of the object is "list_class" it means, the object uri is of a class and so the instances of the class need to be filtered
                # (example: input = Object -> we want search for instances of Object like Bow etc.)
                # for this case rdf:type is used
                if object_category == "list_class":
                    if obj:
                        sparql_part += f"?{side}Description{id} rdf:object ?instancesOfObjectClass .\n"
                        sparql_part += f"?instancesOfObjectClass rdf:type <{obj}> .\n"
                #------------------------------------------------------------- (END) UPDATE by Nico Lambert -----------------------------------------------------------------------------
                else:
                    if obj:
                        sparql_part += f"?{side}Description{id} rdf:object <{obj}> .\n"
        #----------------------------------------------------------- (-END-) UPDATE by Nico Lambert -----------------------------------------------------------------------------
        return sparql_part

    def _eliminate_not_brackets(self, expression):
        """
        Eliminates NOT brackets from a boolean term and returns the resulting expression.

        Parameters:
            expression (str): A boolean expression to be transformed.
        
        Returns:
            str: The transformed boolean expression with eliminated NOT brackets.
        
        Author: Mohammed Sayed Mahmod
        """
        while "NOT (" in expression:
            pattern = r"NOT \(([^)]+)\)"

            def replace_negated_expression(match):
                inner_expression = match.group(1)
                transformed = re.sub(r"\bAND\b", " TEMP_AND ", inner_expression)
                transformed = re.sub(r"\bOR\b", " AND ", transformed)
                transformed = re.sub(r" TEMP_AND ", " OR ", transformed)
                transformed = re.sub(r"(\bC\d+\b)", r"NOT \1", transformed)
                transformed = re.sub(r"NOT NOT ", "", transformed)
                return f"({transformed})"

            booleanTerm = re.sub(pattern, replace_negated_expression, booleanTerm)
            booleanTerm = re.sub(r"NOT NOT ", "", booleanTerm)
            expression = booleanTerm

        expression = re.sub(r"\s+", " ", expression).strip()

        return expression

    def generateQuery(self, coins, booleanTerm, searchType):
        """
        Generates a complete SPARQL query based on a list of coins and a boolean term combining them.
        
        Parameters:
            coins (list): A list of dictionaries, each representing attributes of a coin.
            booleanTerm (str): A boolean expression combining the coins.
            searchType (str): The type of search to be performed.

        Returns:
            str: A complete SPARQL query constructed from the provided coins and boolean term.
        
        Author: Mohammed Sayed Mahmod
        """
        booleanTerm = self._eliminate_not_brackets(booleanTerm)
        booleanTerm = booleanTerm.replace("(", "{").replace(")", "}")

        coin_dict = {f"C{i+1}": (i+1, coin) for i, coin in enumerate(coins)}

        for placeholder, (id, coin_data) in coin_dict.items():
            isNegated = "NOT " + placeholder in booleanTerm
            coinQueryPart = self.generateCoinQuery(id, coin_data, searchType, isNegated)
            booleanTerm = booleanTerm.replace("NOT " + placeholder if isNegated else placeholder, coinQueryPart)


        operators = {
            "AND": "",
            "OR": "UNION"
        }

        for operator, sparql_operator in operators.items():
            booleanTerm = booleanTerm.replace(operator, sparql_operator)

        combined_query = self._query_head
        combined_query += f"SELECT DISTINCT ?url ?thumbnailObverse ?thumbnailReverse ?descriptionObverse ?descriptionReverse ?date ?maxDiameter ?id ?weight ?type ?mint WHERE {{ {booleanTerm} }}"

        return combined_query
    
    
    
    def getRecommendationsPredicate(self, subj_uri, obj_uri, input, side):
        """
        Function that generates a dictionary, which contains a List of dictonaries with each dictonary containing
        a single result of the querried verbs. 

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            input (str): The Input String to be uesd for the Name of the Verb in the Query
            side (str): Coin side of the current input - 'obverse' or 'reverse'
        
        Returns:
            dict: If there is an input, dict contains only verbs which start with the input , otherwise it contains all verbs 
        
        Author: Steven Nowak
        """

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"

        # If there is an input, then the query needs to be filtered, otherwise all verbs are returned (the button for "all verbs" is clicked)
        if input != "":
            query = self.sparqlQueryGetRecomendationsPrediacteWithFilter(input, subj_uri, obj_uri , side)
        else:
            query = self.sparqlQueryGetRecomendationsAllPrediacte(subj_uri, obj_uri , side)       

        query_results = self.executeQuery(query)
        result_dict = {}
        category = "list_verb"
        for row in query_results:
            
            result_item = {
                "link": str(row.pre),
                "name_en": str(row.preName),
            }
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]
        return result_dict
    

    def sparqlQueryGetRecomendationsPrediacteWithFilter(self, input, subj_uri, obj_uri, side):
        """
        Function that generates a SPARQL Query, that returns all verbs, which start with a given input and  
        which occur in a triple with the entered subject and object on the corresponding coin side.
        If there is no entered subject / object it can be any subject / object.

        Parameters:
            input (str): The Input String with which the subject / object has to start with
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            side (str): Coin side of the current input - 'obverse' or 'reverse'
        
        Returns:
            str: SPARQL Query
        
        Author : Nico Lambert
        """

        # ?pre = URI of the verb 
        # ?preName = Name of the verb

        # search after all verbs, which start with the given input
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT DISTINCT ?pre ?preName WHERE{{
                    ?pre <http://www.w3.org/2004/02/skos/core#prefLabel> ?preName .
                    ?pre <http://www.w3.org/2004/02/skos/core#prefLabel> ?Type .
                    FILTER(STRSTARTS(LCASE(?preName), LCASE("{input}")) && STRSTARTS(LCASE(?Type), LCASE("predicate_id"))) .
                """
        
        # user input for subject or object -> extra filter for predicates
        # predicate has to occour (on at least one coin) for the given coin side with the other entered triple elements
        # if for examaple the entered subject is a class like Deities , the predicate has to occur with at least one deity like artemis as subject on the specific coin side
        # if there is no entered object , that mneans it can be any object, doesn't matter which, but it has to be at least once, which is part of a coin triple with the 
        #    the entered subject and the recommendation for the verb.
        if subj_uri != "?s" or obj_uri != "?o":
            query += f"""
                Filter Exists {{
                    ?coinAppearance rdf:predicate ?pre.
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    {{
                        ?coinAppearance rdf:object {obj_uri} .
                    }}
                    UNION
                    {{
                        ?objEntity rdf:type {obj_uri} .
                        ?coinAppearance rdf:object ?objEntity. 
                    }}
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                }}
                }} ORDER BY ASC(?preName)
                """
        # no entered subject / object -> no extra filter
        else:
            query += f"""
                }} ORDER BY ASC(?preName)
                """
        return query
    

    def sparqlQueryGetRecomendationsAllPrediacte(self, subj_uri, obj_uri, side):
        """
        Function that generates a SPARQL Query, that returns all verbs,
        which occur in a triple with the entered subject and object on the corresponding coin side . If there is no entered subject / object it can be any subject / object.
        
        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query

        Author: Nico Lambert
        """

        # ?pre = URI of the verb 
        # ?preName = Name of the verb

        # search after all verbs
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT DISTINCT ?pre ?preName WHERE{{
                    ?pre <http://www.w3.org/2004/02/skos/core#prefLabel> ?preName .
                    ?pre <http://www.w3.org/2004/02/skos/core#prefLabel> ?Type .
                    FILTER(!STRSTARTS(LCASE(?preName), LCASE("predicate_id")) && STRSTARTS(LCASE(?Type), LCASE("predicate_id"))) .
                """
        
        # user input for subject or object -> extra filter for predicates
        # predicate has to occour (on at least one coin) for the given coin side with the other entered triple elements
        # if for examaple the entered subject is a class like Deities , the predicate has to occur with at least one deity like artemis as subject on the specific coin side
        # if there is no entered object , that mneans it can be any object, doesn't matter which, but it has to be at least once, which is part of a coin triple with the 
        #    the entered subject and the recommendation for the verb.
        if subj_uri != "?s" or obj_uri != "?o":
            query += f"""
                Filter Exists {{
                    ?coinAppearance rdf:predicate ?pre.
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    {{
                        ?coinAppearance rdf:object {obj_uri} .
                    }}
                    UNION
                    {{
                        ?objEntity rdf:type {obj_uri} .
                        ?coinAppearance rdf:object ?objEntity. 
                    }}
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                }}
                }} ORDER BY ASC(?preName)
                """
        # no entered subject / object -> no extra filter
        else:
            query += f"""
                }} ORDER BY ASC(?preName)
                """
        return query
    

    def categoryConverter(self, category):
        """
        Function to convert the URI of a category into a string - the name of the category

        Parameters:
            category (str): The URI of the category
        
        Returns:
            str: The name of the category
        
        Author: Steven Nowak
        """
        if category == "https://www.wikidata.org/wiki/Q729":
            return "list_animal"
        elif category == "https://www.wikidata.org/wiki/Q488383":
            return "list_obj"
        elif category == "http://xmlns.com/foaf/0.1/#term_Person":
            return "list_person"
        elif category == "https://www.wikidata.org/wiki/Q756":
            return "list_plant"
        else:
            return "list_unknown"
        
    def sparqlQueryGetRecommendationsSubObjApartFromClasses(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function that generates a SPARQL Query that returns all entities (subjects and objects) which start with the input and are not a class.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        The returned entities are all "leaves". 
        
        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The Input String with which the subject / object has to start with
            side (str): Coin side of the current input - 'obverse' or 'reverse'
        
        Returns:
            str: SPARQL Query

        Author: Nico Lambert
        """

        # ?subOrObj = URI of the entity
        # ?subOrObjName = edit label of the entity / name of the entity
        # ?subOrObjSuperClass = URI of the top Class / Category of the entity

        # search after all entities, which start with the given input and which are only an instance of a class and not a class 
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT DISTINCT ?subOrObj ?subOrObjName ?subOrObjSuperClass WHERE{{
                    ?subOrObj rdf:type ?subOrObjClass .
                    ?subOrObjClass rdfs:subClassOf ?subOrObjSuperClass.
                    ?subOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?subOrObjNameVar.
                    FILTER(!CONTAINS(str(?subOrObjSuperClass), "http://www.w3.org/2000/01/rdf-schema#")).
                    FILTER NOT EXISTS {{
                            ?subOrObjSuperClass rdfs:subClassOf ?anyClass.
                            FILTER(?subOrObjSuperClass != ?anyClass).
                    }}.
                    FILTER((?subOrObjClass != ?subOrObjSuperClass) && (?subOrObj != ?subOrObjSuperClass))
                    BIND(
                        CONCAT(
                            UCASE(SUBSTR(REPLACE(STR(?subOrObjNameVar), "^.*[/_#]", ""), 1, 1)),  
                            LCASE(SUBSTR(REPLACE(STR(?subOrObjNameVar), "^.*[/_#]", ""), 2))     
                        ) AS ?subOrObjName
                    ).
                    FILTER(STRSTARTS(LCASE(?subOrObjName), LCASE("{input}"))).
                """
         
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject 
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":
                query += f"""
                    Filter Exists {{
                        ?coinAppearance rdf:subject ?subOrObj .   
                    """
                if pred_uri != "?p":
                    query += f"""
                        ?coinAppearance rdf:predicate {pred_uri}.
                        """
                if obj_uri != "?o":
                    query += f"""
                        {{
                            ?coinAppearance rdf:object {obj_uri} .
                        }}
                        UNION
                        {{
                            ?objEntity rdf:type {obj_uri} .
                            ?coinAppearance rdf:object ?objEntity. 
                        }}
                        """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.
                query += f"""
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                    ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        ?coinAppearance rdf:li ?subOrObj .
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object 
        else:
            query += f"""
                Filter Exists {{
                    ?coinAppearance rdf:object ?subOrObj .
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """
            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.
            query += f"""
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                    ?coinURI rdf:type nmo:NumismaticObject . 
                }}
                """

        query += f"""
                }} ORDER BY ASC(?subOrObjName)
                """
        
        return query
    

    def sparqlQueryGetRecommendationsSubObjClasses(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function that generates a SPARQL Query that returns all entities (subjects and objects) that are classes, 
        that start with the input. The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        
        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The Input String with which the subject / object has to start with
            side (str): Coin side of the current input - 'obverse' or 'reverse'
        
        Returns:
            str: SPARQL Query

        Author: Nico Lambert
        """

        # ?subOrObjClass = URI of the entity
        # ?subOrObjClassName = edit label of the entity / name of the entity

        # search after all entities, which start with the given input and which are only a class and not an instance of a class 
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT DISTINCT ?subOrObjClass ?subOrObjClassName WHERE{{
                    ?subOrObjClass rdf:type rdfs:Class .
  					?subOrObjClass <http://www.w3.org/2004/02/skos/core#prefLabel> ?subOrObjClassNameVar.
  					BIND(
                        CONCAT(
                            UCASE(SUBSTR(REPLACE(STR(?subOrObjClassNameVar), "^.*[/_#]", ""), 1, 1)),  
                            LCASE(SUBSTR(REPLACE(STR(?subOrObjClassNameVar), "^.*[/_#]", ""), 2))     
                        ) AS ?subOrObjClassName
                    ).
                    FILTER(STRSTARTS(LCASE(STR(?subOrObjClassName)), LCASE("{input}"))).
                    Filter(?subOrObjClass != <http://www.dbis.cs.uni-frankfurt.de/cnt/id/ocre_object_object>).
                    
                """
        
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObjClass.
                        ?coinAppearance rdf:subject ?subjEntity .
                    """
                if pred_uri != "?p":
                    query += f"""
                        ?coinAppearance rdf:predicate {pred_uri}.
                        """
                if obj_uri != "?o":
                    query += f"""
                        {{
                            ?coinAppearance rdf:object {obj_uri} .
                        }}
                        UNION
                        {{
                            ?objEntity rdf:type {obj_uri} .
                            ?coinAppearance rdf:object ?objEntity. 
                        }}
                        """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
                query += f"""
                        ?coinDesignIconography rdf:li ?coinAppearance .
                        ?coinDesignIconography rdf:type rdf:Bag .
                        ?coinIconography nmo:hasIconography ?coinDesignIconography .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObjClass.
                        ?coinAppearance rdf:li ?subjEntity .
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object
        else:
            query += f"""
                Filter Exists {{
                    ?objEntity rdf:type ?subOrObjClass.
                    ?coinAppearance rdf:object ?objEntity.
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """

            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
            query += f"""
                ?coinDesignIconography rdf:li ?coinAppearance .
                ?coinDesignIconography rdf:type rdf:Bag .
                ?coinIconography nmo:hasIconography ?coinDesignIconography .
                ?coinSide nmo:hasIconography ?coinIconography .
                ?coinURI nmo:has{side.capitalize()} ?coinSide .
                ?coinURI rdf:type nmo:NumismaticObject . 
                }}
                """

        query += f"""
                }} ORDER BY ASC(?subOrObjClassName)
                """
        
        return query


    def getRecommendationsSubObj(self, subj_uri, pred_uri, obj_uri, is_subject,  input, side):
        """
        Function to get all Recommendations for a subject or object which starts with the given input. The recommendations sat down together by the 
        results of the three sparql queries that are called in this function :  
            - sparqlQueryGetRecommendationsSubObjApartFromClasses,
            - sparqlQueryGetRecommendationsSubObjClasses
        
        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            dict: contains the Recommendations, keys = categorie names, value = list of dictionaries with keys = 'link' and 'name_en'
            
        Author: Nico Lambert
        """
        result_dict = {}

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        if pred_uri == "":
            pred_uri = "?p" 
        else:
            pred_uri = "<"+pred_uri+">"
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"

        query = self.sparqlQueryGetRecommendationsSubObjApartFromClasses(subj_uri,pred_uri,obj_uri, is_subject, input, side)
        query_results = self.executeQuery(query)
        
        category = ""
        for row in query_results:
            category = self.categoryConverter(str(row.subOrObjSuperClass))
            result_item = {
                "link": str(row.subOrObj),
                "name_en": str(row.subOrObjName),
            }
            
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]

        query = self.sparqlQueryGetRecommendationsSubObjClasses(subj_uri,pred_uri,obj_uri, is_subject, input, side)
        query_results = self.executeQuery(query)
        
        category = "list_class"
        for row in query_results:
            result_item = {
                "link": str(row.subOrObjClass),
                "name_en": str(row.subOrObjClassName),
            }
            
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]
        
        # example for a possible result: dict = {"list_person": [{"name_en": "Artemis", "link": "http:......."}, {..}, .. ], "list_class": [..]}
        return result_dict
    

    def sparqlQueryGetSimpleGeneraliseRecommendationsOfCurrentSubObj(self, input, subj_uri, pred_uri, obj_uri, is_subject, side, filter = ""):
        """
        Function to generate a Query which extracts all Parent Categories 
        of the Current Subject or Object which are exactly one level higher in the Hierachy.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        Used in Function getSimpleGeneraliseRecommendationsOfCurrentSubObj.
        
        Parameters: 
            input (str): The URI of the Current Subject or Object in the Input Field
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Query that dont start with the String
        
        Returns:
            str: A SPARQL Query which can be used to get all Parent Categories of the Current Subject or Object 
            which are exactly one level higher in the Hierachy 

        Author: Steven Nowak
        """

        # ?subOrObj = URI of the entity
        # ?subOrObjName = edit label of the entity / name of the entity

        # search after all entities, respectively after all which start with a given filter if the filter isn't empty, 
        #   which are exactly one level higher in the hierarchy and related to the current selected subject / object
        # The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT Distinct ?subOrObj ?subOrObjName WHERE{{
                    {{
                        <{input}> rdfs:subClassOf ?subOrObj.
                        Filter not exists {{
                            <{input}> rdfs:subClassOf ?anyClass.
                            ?anyClass rdfs:subClassOf ?subOrObj.
                            FILTER(?anyClass != ?subOrObj && ?anyClass != <{input}>).
                        }}
                    }}
                    UNION
                    {{
                        <{input}> rdf:type ?subOrObj.
                        Filter not exists {{
                            <{input}> rdf:type rdfs:Class.
                        }}
                        Filter not exists{{
                            ?subOrObj rdfs:subClassOf <{input}>.
                        }}
                        Filter not exists {{
                            ?subOrObj rdf:type <{input}>.  
                        }}
                        Filter not exists {{
                            <{input}> rdf:type ?anyClass.
                            ?anyClass rdfs:subClassOf ?subOrObj.
                            FILTER(?anyClass != ?subOrObj && ?anyClass != <{input}>).
                        }}
                    }}
                    Filter(?subOrObj != <{input}>).
                    ?subOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?superClassName.
                    BIND(
                        CONCAT(
                            UCASE(SUBSTR(REPLACE(STR(?superClassName), "^.*[/_#]", ""), 1, 1)),  
                            LCASE(SUBSTR(REPLACE(STR(?superClassName), "^.*[/_#]", ""), 2))    
                        ) AS ?subOrObjName
                    ).
                    Filter(Strstarts(Lcase(STR(?subOrObjName)), Lcase("{filter}"))).
                    Filter(?subOrObj != <http://www.dbis.cs.uni-frankfurt.de/cnt/id/ocre_object_object>).
                """
        
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObj.
                        ?coinAppearance rdf:subject ?subjEntity .
                    """
                if pred_uri != "?p":
                    
                    query += f"""
                        ?coinAppearance rdf:predicate {pred_uri}.
                        """

                if obj_uri != "?o":
                    query += f"""
                        {{
                            ?coinAppearance rdf:object {obj_uri} .
                        }}
                        UNION
                        {{
                            ?objEntity rdf:type {obj_uri} .
                            ?coinAppearance rdf:object ?objEntity. 
                        }}
                        """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
                query += f"""
                        ?coinDesignIconography rdf:li ?coinAppearance .
                        ?coinDesignIconography rdf:type rdf:Bag .
                        ?coinIconography nmo:hasIconography ?coinDesignIconography .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                        }}
                        """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObj.
                        ?coinAppearance rdf:li ?subjEntity .
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object       
        else:
            query += f"""
                Filter Exists {{
                    ?objEntity rdf:type ?subOrObj.
                    ?coinAppearance rdf:object ?objEntity.
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side 
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """
            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
            query += f""" 
                ?coinDesignIconography rdf:li ?coinAppearance .
                ?coinDesignIconography rdf:type rdf:Bag .
                ?coinIconography nmo:hasIconography ?coinDesignIconography .
                ?coinSide nmo:hasIconography ?coinIconography .
                ?coinURI nmo:has{side.capitalize()} ?coinSide .
                ?coinURI rdf:type nmo:NumismaticObject .
                }}
                """


        query += f"""
                }} ORDER BY ASC(?subOrObjName)
                """
        return query

    

    def sparqlQueryGetSimpleSpecializRecommendationsOfCurrentSubObj(self, input, subj_uri, pred_uri, obj_uri, is_subject, side, filter = ""): 
        """
        Function to generate a Query which extracts all Child Categories  
        of the Current Subject or Object which are exactly one level Lower in the Hierachy.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        Used in Function getSimpleSpecializRecommendationsOfCurrentSubObj.
        
        Parameters: 
            input (str): The URI of the Current Subject or Object in the Input Field
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Query that dont start with the String
        
        Returns:
            str: A SPARQL Query which can be used to extracts all Child Categories 
                 of the Current Subject or Object which are exactly one level Lower in the Hierachy.
        Author: Steven Nowak
        """

        # ?subOrObj = URI of the entity
        # ?subOrObjName = edit label of the entity / name of the entity
        # search after all entities, respectively after all which start with a given filter if the filter isn't empty, 
        #   which are exactly one level lower in the hierarchy and related to the current selected subject / object
        # The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT Distinct ?subOrObj ?subOrObjName WHERE{{
                    ?subOrObj rdfs:subClassOf <{input}> .
                    Filter not exists {{
                        ?subOrObj rdfs:subClassOf ?anyClass.
                        ?anyClass rdfs:subClassOf <{input}>.
                        FILTER(?subOrObj != ?anyClass && ?anyClass != <{input}>).
                    }}
                    Filter(?subOrObj != <{input}>).
                    ?subOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?subClassName .
  					BIND(
                        CONCAT(
                            UCASE(SUBSTR(REPLACE(STR(?subClassName), "^.*[/_#]", ""), 1, 1)),  
                            LCASE(SUBSTR(REPLACE(STR(?subClassName), "^.*[/_#]", ""), 2))     
                        ) AS ?subOrObjName
                    ).
                    Filter(Strstarts(Lcase(STR(?subOrObjName)), Lcase("{filter}"))).
                    Filter(?subOrObj != <http://www.dbis.cs.uni-frankfurt.de/cnt/id/ocre_object_object>).
                """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObj.
                        ?coinAppearance rdf:subject ?subjEntity .
                    """
                if pred_uri != "?p":
                    
                    query += f"""
                        ?coinAppearance rdf:predicate {pred_uri}.
                        """

                if obj_uri != "?o":

                    query += f"""
                        {{
                            ?coinAppearance rdf:object {obj_uri} .
                        }}
                        UNION
                        {{
                            ?objEntity rdf:type {obj_uri} .
                            ?coinAppearance rdf:object ?objEntity. 
                        }}
                        """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
                query += f"""
                        ?coinDesignIconography rdf:li ?coinAppearance .
                        ?coinDesignIconography rdf:type rdf:Bag .
                        ?coinIconography nmo:hasIconography ?coinDesignIconography .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                        }}
                        """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObj.
                        ?coinAppearance rdf:li ?subjEntity .
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object        
        else:
            query += f"""
                Filter Exists {{
                    ?objEntity rdf:type ?subOrObj.
                    ?coinAppearance rdf:object ?objEntity.
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """
            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
            query += f""" 
                ?coinDesignIconography rdf:li ?coinAppearance .
                ?coinDesignIconography rdf:type rdf:Bag .
                ?coinIconography nmo:hasIconography ?coinDesignIconography .
                ?coinSide nmo:hasIconography ?coinIconography .
                ?coinURI nmo:has{side.capitalize()} ?coinSide .
                ?coinURI rdf:type nmo:NumismaticObject .
                }}
                """


        query += f"""
                }} ORDER BY ASC(?subOrObjName)
                """
        return query
    
    def sparqlQueryGetAbsoluteGeneraliseRecommendationsOfCurrentSubObj(self, input, subj_uri, pred_uri, obj_uri, is_subject, side, filter = ""):
        """
        Function to generate a Query which extracts the Parent Categorie
        of the Current Subject or Object which is on the highest level in the Hierachy.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        Used in Function getAbsoluteGeneraliseRecommendationsOfCurrentSubObj.
        
        Parameters: 
            input (str): The URI of the Current Subject or Object in the Input Field
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Query that dont start with the String
        
        Returns:
            str: A SPARQL Query which can be used extracts the Parent Categorie
            of the Current Subject or Object which is on the highest level in the Hierachy.
        Author: Steven Nowak
        """

        # ?subOrObj = URI of the entity
        # ?subOrObjName = edit label of the entity / name of the entity
        # search after all entities, respectively after all which start with a given filter if the filter isn't empty, 
        #   which are on top level in the hierarchy and related to the current selected subject / object
        # The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT Distinct ?subOrObj ?subOrObjName WHERE{{
                    {{
                        <{input}> rdfs:subClassOf ?subOrObj.
                    }}
                    UNION
                    {{
                        <{input}> rdf:type ?subOrObj.
                        Filter not exists {{
                            <{input}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Class>.
                        }}
                    }}
                    Filter not exists {{
                        ?subOrObj rdfs:subClassOf ?anyClass.
                        FILTER(?subOrObj != ?anyClass).
                    }}
                    Filter(?subOrObj != <{input}>).
                    ?subOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?superClassName.
                    BIND(
                        CONCAT(
                            UCASE(SUBSTR(REPLACE(STR(?superClassName), "^.*[/_#]", ""), 1, 1)),  
                            LCASE(SUBSTR(REPLACE(STR(?superClassName), "^.*[/_#]", ""), 2))      
                        ) AS ?subOrObjName
                    ).
                    Filter(Strstarts(Lcase(STR(?subOrObjName)), Lcase("{filter}"))).
                """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObj.
                        ?coinAppearance rdf:subject ?subjEntity .
                    """
                if pred_uri != "?p":
                    
                    query += f"""
                        ?coinAppearance rdf:predicate {pred_uri}.
                        """

                if obj_uri != "?o":

                    query += f"""
                        {{
                            ?coinAppearance rdf:object {obj_uri} .
                        }}
                        UNION
                        {{
                            ?objEntity rdf:type {obj_uri} .
                            ?coinAppearance rdf:object ?objEntity. 
                        }}
                        """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
                query += f"""
                        ?coinDesignIconography rdf:li ?coinAppearance .
                        ?coinDesignIconography rdf:type rdf:Bag .
                        ?coinIconography nmo:hasIconography ?coinDesignIconography .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                        }}
                        """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        ?subjEntity rdf:type ?subOrObj.
                        ?coinAppearance rdf:li ?subjEntity .
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object        
        else:
            query += f"""
                Filter Exists {{
                    ?objEntity rdf:type ?subOrObj.
                    ?coinAppearance rdf:object ?objEntity.
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """
            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.      
            query += f""" 
                ?coinDesignIconography rdf:li ?coinAppearance .
                ?coinDesignIconography rdf:type rdf:Bag .
                ?coinIconography nmo:hasIconography ?coinDesignIconography .
                ?coinSide nmo:hasIconography ?coinIconography .
                ?coinURI nmo:has{side.capitalize()} ?coinSide .
                ?coinURI rdf:type nmo:NumismaticObject .
                }}
                """


        query += f"""
                }} ORDER BY ASC(?subOrObjName)
                """
        return query

    

    def sparqlQueryGetAbsoluteSpecializRecommendationsOfCurrentSubObj(self, input, subj_uri, pred_uri, obj_uri, is_subject, side, filter = ""):
        """
        Function to generate a Query which extracts all Child Entities of the Current Subject or Object.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        Used in Function getSimpleSpecializRecommendationsOfCurrentSubObj and getAbsoluteSpecializRecommendationsOfCurrentSubObj.
        
        Parameters: 
            input (str): The URI of the Current Subject or Object in the Input Field
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Query that dont start with the String
        
        Returns:
            str: A SPARQL Query which can be used to extracts all Child Categories or Entities 
                 of the Current Subject or Object which are exactly one level Lower in the Hierachy.
        Author: Steven Nowak
        """

        # ?subOrObj = URI of the entity
        # ?subOrObjName = edit label of the entity / name of the entity
        # ?superClass = URI of the top superclass of the entity
        # search after all entities, respectively after all which start with a given filter if the filter isn't empty, 
        #   which are exactly on the bottom of the hierarchy and related to the current selected subject / object
        # The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT Distinct ?subOrObj ?subOrObjName ?superClass WHERE{{
                    OPTIONAL{{
                        <{input}> rdfs:subClassOf ?superClass .
                        Filter not exists {{
                            ?superClass rdfs:subClassOf ?anyClass.
                            FILTER(?superClass != ?anyClass).
                        }}
                    }}
                    ?subOrObj rdf:type <{input}>.
                    Filter not exists {{
                        ?subOrObj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Class>.
                    }}
  					?subOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?leafName.
  					BIND(
                        CONCAT(
                            UCASE(SUBSTR(REPLACE(STR(?leafName), "^.*[/_#]", ""), 1, 1)),  
                            LCASE(SUBSTR(REPLACE(STR(?leafName), "^.*[/_#]", ""), 2))    
                        ) AS ?subOrObjName
                    ).
                    Filter(Strstarts(Lcase(STR(?subOrObjName)), Lcase("{filter}"))).
                """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":

                query += f"""
                    Filter Exists {{
                        ?coinAppearance rdf:subject ?subOrObj .
                    """
                if pred_uri != "?p":
                    query += f"""
                            ?coinAppearance rdf:predicate {pred_uri}.
                        """

                if obj_uri != "?o":
                    query += f"""
                            {{
                                ?coinAppearance rdf:object {obj_uri} .
                            }}
                            UNION
                            {{
                                ?objEntity rdf:type {obj_uri} .
                                ?coinAppearance rdf:object ?objEntity. 
                            }}
                        """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
                query += f"""
                        ?coinDesignIconography rdf:li ?coinAppearance .
                        ?coinDesignIconography rdf:type rdf:Bag .
                        ?coinIconography nmo:hasIconography ?coinDesignIconography .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        ?coinAppearance rdf:li ?subOrObj .
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object
        else:
            query += f"""
                Filter Exists {{
                    ?coinAppearance rdf:object ?subOrObj .
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """
            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.      
            query += f"""
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                    ?coinURI rdf:type nmo:NumismaticObject . 
                }}
                """

        query += f"""
                }} ORDER BY ASC(?subOrObjName)
                """
        return query

 


    def sparqlQueryGetEquivalentRecommendationsToCurrentSubObj(self, input, subj_uri, pred_uri, obj_uri, is_subject, side, filter = ""):
        """
        Function to generate a Query which extracts all direct Child Entities of the parent Entities of the current Subject or Object.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        
        Parameters: 
            input (str): The URI of the Current Subject or Object in the Input Field
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Query that dont start with the String
        
        Returns:
            str: SPAQRQL Query
        
        Author: Nico Lambert
        """

        # ?toInputEquivalentSubOrObj = URI of the to the selected entity equivalent entity
        # ?toInputEquivalentSubOrObjName = edit label of the to the selected entity equivalent entity / name of the to the selected entity equivalent entity
        # ?superClass = URI of the top superclass of the to the selected entity equivalent entity
        # search after all entities, respectively after all which start with a given filter if the filter isn't empty, 
        #   which are on the same level in the hierarchy and related to the current selected subject / object
        # The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        query = f"""
                PREFIX nmo: <http://nomisma.org/ontology#>
                SELECT DISTINCT ?toInputEquivalentSubOrObj ?toInputEquivalentSubOrObjName ?superClass  WHERE {{
                    OPTIONAL{{
                        <{input}> rdf:type ?superClass .
                        Filter NOT EXISTS {{
                            ?superClass rdfs:subClassOf ?anyClass.
                            FILTER(?superClass != ?anyClass).
                            
                        }}
                        FILTER NOT EXISTS {{
                            <{input}> rdf:type rdfs:Class.
                        }}
                    }}
        	        {{
                        <{input}> rdfs:subClassOf ?simpleGeneralization.
                        FILTER NOT EXISTS {{
                            <{input}> rdfs:subClassOf ?anyClass.
                            ?anyClass rdfs:subClassOf ?simpleGeneralization.
                            FILTER(?anyClass != ?simpleGeneralization && ?anyClass != <{input}>).
                        }}
                        ?toInputEquivalentSubOrObj rdfs:subClassOf ?simpleGeneralization .

                        Filter NOT EXISTS {{
                            ?toInputEquivalentSubOrObj rdfs:subClassOf ?anyClass.
                            ?anyClass rdfs:subClassOf ?simpleGeneralization.
                            FILTER(?toInputEquivalentSubOrObj != ?anyClass && ?toInputEquivalentSubOrObj != ?simpleGeneralization).
                        }}
                        Filter(?toInputEquivalentSubOrObj != ?simpleGeneralization).
                        ?toInputEquivalentSubOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?equivalentSubOrObjName .
                        BIND(
                            CONCAT(
                                UCASE(SUBSTR(REPLACE(STR(?equivalentSubOrObjName), "^.*[/_#]", ""), 1, 1)),  
                                LCASE(SUBSTR(REPLACE(STR(?equivalentSubOrObjName), "^.*[/_#]", ""), 2))     
                            ) AS ?toInputEquivalentSubOrObjName
                        ).
                    }}
                    UNION
                    {{
                        <{input}> rdf:type ?simpleGeneralization.
                        FILTER NOT EXISTS {{ <{input}> rdf:type rdfs:Class. }}
                        FILTER NOT EXISTS {{ ?simpleGeneralization rdfs:subClassOf <{input}>. }}
                        FILTER NOT EXISTS {{ ?simpleGeneralization rdf:type <{input}>. }}
                        FILTER NOT EXISTS {{
                            <{input}> rdf:type ?anyClass.
                            ?anyClass rdfs:subClassOf ?simpleGeneralization.
                            FILTER(?anyClass != ?simpleGeneralization && ?anyClass != <{input}>).
                        }}
                        ?toInputEquivalentSubOrObj rdf:type ?simpleGeneralization .
                        FILTER NOT EXISTS {{
                            ?toInputEquivalentSubOrObj rdfs:subClassOf ?anyClass.
                            FILTER(?simpleGeneralization != ?anyClass).
                        }}
                        Filter(?toInputEquivalentSubOrObj != ?simpleGeneralization).
                        ?toInputEquivalentSubOrObj <http://www.w3.org/2004/02/skos/core#prefLabel> ?equivalentSubOrObjName .
                        BIND(
                            CONCAT(
                                UCASE(SUBSTR(REPLACE(STR(?equivalentSubOrObjName), "^.*[/_#]", ""), 1, 1)),  
                                LCASE(SUBSTR(REPLACE(STR(?equivalentSubOrObjName), "^.*[/_#]", ""), 2))     
                            ) AS ?toInputEquivalentSubOrObjName
                        ).
                    }}
                    Filter(Strstarts(Lcase(STR(?toInputEquivalentSubOrObjName)), Lcase("{filter}"))) .
                    FILTER(?simpleGeneralization != <{input}>).
  	                FILTER(?toInputEquivalentSubOrObj != <{input}>).
                """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a subject
        if (is_subject == "true"): 
            # searched entities have to occour in a triple (on at least one coin) for the given coin side with the other entered triple elements.
            # if the entered object is a class like animal , the entity has to occur in a triple (on at least one coin) for the given coin side with 
            #    the entered predicate and any animal, otherwise with the entered predicate and the specific object
            # if predicate / object isn't entered yet it can be any predicate / object
            if pred_uri != "?p" or obj_uri != "?o":
                query += f"""
                    Filter Exists {{
                        {{
                            ?coinAppearance rdf:subject ?toInputEquivalentSubOrObj .
                        }}
                        UNION
                        {{
                            ?subjEntity rdf:type ?toInputEquivalentSubOrObj.
                            ?coinAppearance rdf:subject ?subjEntity .
                        }}
                    """
                if pred_uri != "?p":
                    query += f"""
                        ?coinAppearance rdf:predicate {pred_uri}.
                        """
                
                if obj_uri != "?o":
                    query += f"""
                        {{
                        ?coinAppearance rdf:object {obj_uri} .
                        }}
                        UNION
                        {{
                            ?objEntity rdf:type {obj_uri} .
                            ?coinAppearance rdf:object ?objEntity. 
                        }}
                    """
                # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.  
                query += f"""
                        ?coinDesignIconography rdf:li ?coinAppearance .
                        ?coinDesignIconography rdf:type rdf:Bag .
                        ?coinIconography nmo:hasIconography ?coinDesignIconography .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .
                        ?coinURI rdf:type nmo:NumismaticObject . 
                    }}
                    """
            # no entered predicate and no entered object 
            # searched entities only have to occur on at least one coin (with type numismatic object) for the given coin side -> single word search
            else:
                query += f"""
                    Filter Exists {{
                        {{
                            ?coinAppearance rdf:li ?toInputEquivalentSubOrObj .
                        }}
                        UNION
                        {{
                            ?subjEntity rdf:type ?toInputEquivalentSubOrObj.
                            ?coinAppearance rdf:li ?subjEntity 
                        }}
                        ?coinIconography nmo:hasAppearance ?coinAppearance .
                        ?coinSide nmo:hasIconography ?coinIconography .
                        ?coinURI nmo:has{side.capitalize()} ?coinSide .   
                        ?coinURI rdf:type nmo:NumismaticObject . 

                    }}
                    """
        # searched entitities have to occur in a triple (on at least one coin) for the given coin side as a object      
        else:
            query += f"""
                Filter Exists {{
                    ?coinAppearance rdf:object ?toInputEquivalentSubOrObj .
                """
            # if the entered subject is a class like deities , the entity has to occur in a triple (on at least one coin) for the given coin side with any deity, otherwise with
            #    the specif entered subject
            if subj_uri != "?s":
                query += f"""
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    """
            # if the user entered a predicate the object has to occur with it in a triple (on at least one coin) for the given coin side
            if pred_uri != "?p":
                query += f"""
                    ?coinAppearance rdf:predicate {pred_uri}.
                    """
            # the searched entities have to be in a triple for the given coin side, on at least one coin which has the type numismatic object.      
            query += f"""
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                    ?coinURI rdf:type nmo:NumismaticObject . 
                }}
                """

        query += f"""
                }} ORDER BY ASC(?toInputEquivalentSubOrObjName)
                """
        return query



    def getSimpleGeneraliseRecommendationsOfCurrentSubObj(self, subj_uri, pred_uri, obj_uri, is_subject, side, filter=""):
        """
        Function to generate the Recommandation for the Parent Categories of the current Subject or Object which are exactly one level higher in the Hierachy.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        
        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Recommandation that dont start with the String
        
        Returns:
            dict: Recommendations based on the SPARQL Query

        Author: Nico Lambert
        """
        result_dict = {}
        
        input = ""
        if (is_subject == "true") : # is_subject is a boolean but python interprets it as string when it is handed over
            input = subj_uri
        else :
            input = obj_uri

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        if pred_uri == "":
            pred_uri = "?p" 
        else:
            pred_uri = "<"+pred_uri+">"
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"
        
        query = self.sparqlQueryGetSimpleGeneraliseRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, filter)
        query_results = self.executeQuery(query)
        
        category = "list_class"
        for row in query_results:
            result_item = {
                "link": str(row.subOrObj),
                "name_en": str(row.subOrObjName),
            }
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]
        return result_dict
    
    def getSimpleSpecializRecommendationsOfCurrentSubObj(self, subj_uri, pred_uri, obj_uri, is_subject, side, filter=""):
        """
        Function to generate the Recommandation for the Child Categories or Entities of the current Subject or Object which are exactly one level lower in the Hierachy.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        
        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Recommandation that dont start with the String
        
        Returns:
            dict: Recommendations based on the SPARQL Query

        Author: Nico Lambert
        """

        result_dict = {}

       
        if (is_subject == "true" ) : # is_subject is a boolean but python interprets it as string when it is handed over
            input = subj_uri
        else :
            input = obj_uri

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        if pred_uri == "":
            pred_uri = "?p" 
        else:
            pred_uri = "<"+pred_uri+">"
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"

        query = self.sparqlQueryGetSimpleSpecializRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, filter)
        query_results = self.executeQuery(query)
        if len(query_results) > 0:
            category = "list_class"
            for row in query_results:
                result_item = {
                    "link": str(row.subOrObj),
                    "name_en": str(row.subOrObjName),
                }
                if category in result_dict:
                    result_dict[category].append(result_item)
                else:
                    result_dict[category] = [result_item]
        else:
            query = self.sparqlQueryGetAbsoluteSpecializRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, filter)
            query_results = self.executeQuery(query)
            for row in query_results:
                category = self.categoryConverter(str(row.superClass))
                result_item = {
                    "link": str(row.subOrObj),
                    "name_en": str(row.subOrObjName),
                }
                if category in result_dict:
                    result_dict[category].append(result_item)
                else:
                    result_dict[category] = [result_item]
        

        return result_dict
    
    def getAbsoluteGeneraliseRecommendationsOfCurrentSubObj(self, subj_uri, pred_uri, obj_uri, is_subject, side, filter=""):
        """
        Function to generate the Recommandation for the Parent Categories of the current Subject or Object which is on the highest Level of the Hierachy.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.
        
        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Recommandation that dont start with the String
        
        Returns:
            dict: Recommendations based on the SPARQL Query

        Author: Nico Lambert
        """
        result_dict = {}



        input = ""
        if (is_subject == "true") : # is_subject is a boolean but python interprets it as string when it is handed over
            input = subj_uri
        else :
            input = obj_uri

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        if pred_uri == "":
            pred_uri = "?p" 
        else:
            pred_uri = "<"+pred_uri+">"
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"


        query = self.sparqlQueryGetAbsoluteGeneraliseRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, filter)
        query_results = self.executeQuery(query)
        
        category = "list_class"
        for row in query_results:
            result_item = {
                "link": str(row.subOrObj),
                "name_en": str(row.subOrObjName),
            }
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]
        
        return result_dict
    
    def getAbsoluteSpecializRecommendationsOfCurrentSubObj(self, subj_uri, pred_uri, obj_uri, is_subject, side, filter=""):
        """
        Function to generate the Recommandation for the Child Entities of the current Subject or Object.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.

        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Recommandation that dont start with the String
        
        Returns:
            dict: Recommendations based on the SPARQL Query

        Author: Nico Lambert
        """
        result_dict = {}


        input = ""
        if (is_subject == "true") : # is_subject is a boolean but python interprets it as string when it is handed over
            input = subj_uri
        else :
            input = obj_uri

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        if pred_uri == "":
            pred_uri = "?p" 
        else:
            pred_uri = "<"+pred_uri+">"
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"
        query = self.sparqlQueryGetAbsoluteSpecializRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, filter)
        query_results = self.executeQuery(query)
        for row in query_results:
            if row.superClass != None:
                category = self.categoryConverter(str(row.superClass))
            else:
                category = self.categoryConverter(str(input)); 
            result_item = {
                "link": str(row.subOrObj),
                "name_en": str(row.subOrObjName),
            }
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]

        return result_dict


    def getEquivalentRecommendationsToCurrentSubObj(self, subj_uri, pred_uri, obj_uri, is_subject, side, filter=""):
        """
        Function to generate the Recommandation for equivalent Entities of the current Subject or Object.
        The entities also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.

        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            side (str): Coin side of the current input - 'obverse' or 'reverse'
            filter (str): User based Input that Removes all Categories from the Recommandation that dont start with the String
        
        Returns:
            dict: Recommendations based on the SPARQL Query
            
        Author: Nico Lambert
        """
        result_dict = {}

        input = ""
        if (is_subject == "true") : # is_subject is a boolean but python interprets it as string when it is handed over
            input = subj_uri
        else :
            input = obj_uri

        if subj_uri == "":
            subj_uri = "?s"
        else:
            subj_uri = "<"+subj_uri+">" 
        if pred_uri == "":
            pred_uri = "?p" 
        else:
            pred_uri = "<"+pred_uri+">"
        if obj_uri == "":
            obj_uri = "?o" 
        else:
            obj_uri = "<"+obj_uri+">"
        query = self.sparqlQueryGetEquivalentRecommendationsToCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, filter)
        query_results = self.executeQuery(query)

        for row in query_results:
            if row.superClass == None :
                category = "list_class"
            else:
                category = self.categoryConverter(str(row.superClass))
            result_item = {
                "link": str(row.toInputEquivalentSubOrObj),
                "name_en": str(row.toInputEquivalentSubOrObjName),
            }
            if category in result_dict:
                result_dict[category].append(result_item)
            else:
                result_dict[category] = [result_item]
        return result_dict


    def sparqlQueryAreGeneraliseRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function to generate a SPARQL Query, that checks if at least one generalisation recommendation exists for the current Subject or Object

        Parameters: 
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query 

        Author: Nico Lambert
        """
        query = self.sparqlQueryGetSimpleGeneraliseRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, "")
        query += f"""
            LIMIT 1
            """
        return query

    def areGeneraliseRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function to check, if at least one generalisation recommendation exists for the current Subject or Object

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: Strings that shows if at least one Generalisation Recommendation exists for the current Subject or Object
                true: At least one Generalisation Recommendation exists
                false: No Generalisation Recommendation exists
        
        Author: Nico Lambert
        """
        query = self.sparqlQueryAreGeneraliseRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, input, side)
        query_results = self.executeQuery(query)
        if (len(query_results) > 0):
            return "true"
        else:
            return "false"

    
    def sparqlQueryAreSpecialiseRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function to generate a SPARQL Query, that checks if at least one specialisation recommendation exists for the current Subject or Object

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query that checks if at least one Specialisation Recommendation exists for the current Subject or Object
            
        Author: Nico Lambert
        """
        query = self.sparqlQueryGetAbsoluteSpecializRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, "")
        query += f"""
            LIMIT 1
            """
        
        return query
    
    def sparqlQueryAreSpecialiseClassRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function to generate a SPARQL Query, that checks if at least one specialisation recommendation from type class exists for the current Subject or Object

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query that checks if at least one Specialisation Recommendation from type class exists for the current Subject or Object
            
        Author: Nico Lambert
        """
        query = self.sparqlQueryGetSimpleSpecializRecommendationsOfCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, "")
        query += f"""
            LIMIT 1
            """
        
        return query

    def areSpecialiseRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function that checks if at least one specialisation recommendation exists for the current Subject or Object

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: Strings that shows if at least one Specialisation Recommendation exists  
                true: At least one Specialisation Recommendation exists
                false: No Specialisation Recommendation exists

        Author: Nico Lambert
        """
        
        query = self.sparqlQueryAreSpecialiseRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, input, side)

        query_results = self.executeQuery(query)

        
        if (len(query_results) > 0):
            return "true"
        else:
            query = self.sparqlQueryAreSpecialiseClassRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, input, side)
            query_results = self.executeQuery(query)
            if (len(query_results) > 0):
                return "true"
            else:
                return "false"
        
    def sparqlQueryAreEquivalentRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function to generate a SPARQL Query, that checks if at least one equivalent recommendation exists for the current Subject or Object

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query that checks if at least one Equivalent Recommendation exists
        
        Author: Steven Nowak
        """
        query = self.sparqlQueryGetEquivalentRecommendationsToCurrentSubObj(input, subj_uri, pred_uri, obj_uri, is_subject, side, "")
        query += f"""
            LIMIT 1
            """
        
        return query

    def areEquivalentRecommendationsOfCurrentTagAvailable(self, subj_uri, pred_uri, obj_uri, is_subject, input, side):
        """
        Function that checks if at least one sibling entity for the current entity exists for the current coin side
        The entity also have to occur in a triple (on at least one coin) for the given coin side with the other entered triple elements.

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            pred_uri (str): The URI of the Current Predicate on the Coin Side the Function is triggered on
            obj_uri (str): The URI of the Current Object on the Coin Side the Function is triggered on
            is_subject (str): Can be true or false -> true means current input is for subject, otherwise object
            input (str): The URI of the Current Subject or Object in the Input Field
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: String that shows if at least one Equivalent Recommendation exists
                 true: At least one Equivalent Recommendation exists
                 false: No Equivalent Recommendation exists
        
        Author: Steven Nowak
        """
        
        query = self.sparqlQueryAreEquivalentRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, input, side)
        query_results = self.executeQuery(query)
        
        if (len(query_results) > 0):
            return "true"
        else:
            return "false"
        

    def sparqlQueryAreRecommendationsAvailable(self, subj_uri, side):
        """
        Function to generate a SPARQL Query, that checks if at least one Predicate and one Object Recommendation exist for the current Subject

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query that checks if at least one Predicate and Object Recommendation exists for the current coin side
        
        Author: Steven Nowak
        """

        # ?coinURI = URI of a coin which contains a triple with the current selected triple for the given coin side
        # search after one coin uri which contains a triple with the current selected triple for the given coin side
        query = f"""
            PREFIX nmo: <http://nomisma.org/ontology#>
            SELECT DISTINCT ?coinURI WHERE{{
                Filter Exists {{
                    {{
                        ?coinAppearance rdf:subject {subj_uri} .
                    }}
                    UNION
                    {{
                        ?subEntity rdf:type {subj_uri} .
                        ?coinAppearance rdf:subject ?subEntity. 
                    }}
                    ?coinDesignIconography rdf:li ?coinAppearance .
                    ?coinDesignIconography rdf:type rdf:Bag .
                    ?coinIconography nmo:hasIconography ?coinDesignIconography .
                    ?coinSide nmo:hasIconography ?coinIconography .
                    ?coinURI nmo:has{side.capitalize()} ?coinSide .
                    ?coinURI rdf:type nmo:NumismaticObject . 
                }}
            }} Limit 1
                """
        return query 
    
    def areRecommendationsAvailable(self, subj_uri, side):  
        """
        Function that checks if at least one Predicate and Object Recommendation exists for the current coin side
        by looking for at least one coin with the Subject in a Triple Relation for the current coin side

        Parameters:
            subj_uri (str): The URI of the Current Subject on the Coin Side the Function is triggered on 
            side (str): Coin side of the current input - 'obverse' or 'reverse'

        Returns:
            str: SPARQL Query that checks if at least one Predicate and Object Recommendation exists for the current coin side
                 true: At least one Predicate and one Object Recommendation exists for the current coin side
                 false: No Predicate and one Object Recommendation exists for the current coin side

        Author: Steven Nowak
        """
        query = self.sparqlQueryAreRecommendationsAvailable(subj_uri, side)

        query_results = self.executeQuery(query)
        if(len(query_results) > 0):
            return "true"
        else:
            return "false"
        
