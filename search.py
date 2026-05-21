import json
from math import log
from nltk.stem import PorterStemmer
import regex as re

STEMMER = PorterStemmer()
    
def process_query_to_token(query: str):
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    stemmed = [STEMMER.stem(token) for token in tokens]

    return set(stemmed)

def search(query_tokens: set) -> dict:
    with open("final_index.json", "r", encoding="utf-8") as f:
        index = json.load(f)

    token_postings_dict = {}
    for token in query_tokens:
        posting_list = index.get(token)
        if posting_list == None:
            continue
        token_postings_dict[token] = posting_list

    return token_postings_dict
    

def calc_tfidf(tf: int, df: int, n: int) -> float:
     # code:
    # total_docs = len(idIndex)
    # idf = {}
    # for token, postings in p_lists.items():
        # idf[token] = log(docID / len(p_lists))
    
    # boolean AND
    # store freq * idf[token] ...
    weighed_tf = 1 + log(tf, 10)
    weighed_idf = log((n/df), 10)

    return weighed_tf * weighed_idf

def get_intersection(search_postings_dict: dict, total_n) -> dict:
    if not search_postings_dict:
        return {}
    sorted_search_postings_dict = dict(sorted(search_postings_dict.items(), key=lambda x: len(x[1])))
    # get only shortest p list to compare
    first_token = next(iter(sorted_search_postings_dict))
    intersection_docs = {} # INITIALIZED - NATH
    for p in sorted_search_postings_dict[first_token]:
        intersection_docs[p["doc_ID"]] = calc_tfidf(p["freq"], len(sorted_search_postings_dict[first_token]), total_n) # len(sorted_search_postings_dict[first_token]) instead of len(p) - NATH
    
    # boolean and
    for token, p_list in list(sorted_search_postings_dict.items())[1:]:
        
        current = dict()
        for p in p_list:
            current[p["doc_ID"]] = calc_tfidf(p["freq"], len(p_list), total_n) # len(p_list) instead len(p) - NATH
        
        update_intersection = dict()
        for docID in intersection_docs:
            if docID in current:
                update_intersection[docID] = current[docID] + intersection_docs[docID]
        intersection_docs = update_intersection
    
    return intersection_docs
   
def rank_frequencies(intersection_docs: dict) -> list: # imp tf-idf here?
    if not intersection_docs:
        return []
    result = sorted(intersection_docs.items(), key=lambda x: -x[1]) # this turns into a tuple?

    to_show = 5 if len(result) >= 5 else len(result)
    return result[:to_show]

def get_URLs_from_doc(top5docs: dict) -> dict: 
    asURL = {}
    if top5docs:
        with open("doc_id_to_url.json", "r", encoding="utf-8") as file:
            idIndex = json.load(file)
        
        #print(len(idIndex))
        
        for doc, score in (top5docs): # TOOK OUT ENUMERATE -NATH
            asURL[(idIndex[str(doc)])] = score # .json's always store keys as strings, TOOK OUT int()

    return asURL

def print_URLs_and_scores(url_dict: dict) -> None:
    if not url_dict:
        print("No results found.\n")
        return

    n = 1
    print(f"Top {len(url_dict)} Results:")
    for url, score in url_dict.items(): # TOOK OUT enumerate - NATH
        print(f"{n}. {url}  |||  Relevance Score: {score}")
        n += 1

    if len(url_dict) < 5:
        print(f"Only found {len(url_dict)} results.")
    print()
    return

def query(total_n_docs: int) -> None:  
    user_query = input("Please enter your query (type '-QUIT-' to quit): ")
    if user_query == "-QUIT-":
        return
    
    query_as_tokens = process_query_to_token(user_query)
    if query_as_tokens:
        full_search = search(query_as_tokens)
        #if full_search: #COMMENTED OUT - NATH
        boolean_search = get_intersection(full_search, total_n_docs)
        top5_docID = rank_frequencies(boolean_search)
        # print(top5_docID) # REMOVE LATER
        
        top5_URL = get_URLs_from_doc(top5_docID) 
        print_URLs_and_scores(top5_URL) 
    else:
        print("Empty query. No results.\n")
    query(total_n_docs)
