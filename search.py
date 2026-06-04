import json
from math import log
from nltk.stem import PorterStemmer
import regex as re
from time import perf_counter

STEMMER = PorterStemmer()
    
def process_query_to_token(query: str):
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    stemmed = [STEMMER.stem(token) for token in tokens]

    return set(stemmed)

def search(query_tokens: set) -> dict:
    with open("seek_table.json", "r", encoding="utf-8") as f:
        seek_table = json.load(f)

    token_postings_dict = {}
    with open("final_index.json", "r", encoding="utf-8") as f:
        for token in query_tokens:
            offset = seek_table.get(token)
            if offset is None:
                continue
            f.seek(offset)
            line = f.readline()
            token_postings_dict[token] = json.loads(line)[token]

    # M2 implementation for loading entire index into memory            
    # for token in query_tokens:
    #     posting_list = index.get(token)
    #     if posting_list == None:
    #         continue
    #     token_postings_dict[token] = posting_list

    return token_postings_dict
    

def calc_tfidf(tf: int, df: int, n: int, imp_freq: int = 0) -> float:
     # code:
    # total_docs = len(idIndex)
    # idf = {}
    # for token, postings in p_lists.items():
        # idf[token] = log(docID / len(p_lists))
    
    # boolean AND
    # store freq * idf[token] ...
    weighed_tf = 1 + log(tf, 10)
    weighed_idf = log((n/df), 10)
    boost = 1 + log(1 + imp_freq, 10)

    return weighed_tf * weighed_idf * boost

def get_intersection(search_postings_dict: dict, total_n) -> dict:
    if not search_postings_dict:
        return {}
    
    # structure (token: posting list), (token2: posting list)
    sorted_search_postings_dict = dict(sorted(search_postings_dict.items(), key=lambda x: len(x[1])))
    
    # Posting[positions] have all the position of the that token
    # want positions_docs: {doc_id1: {token1: [pos1, pos2], token2: [pos1]}, doc_id2:...}

    # start only with the first posting (shortest length=rarest word -> token appears in least amount of docs) 
    first_token = next(iter(sorted_search_postings_dict)) # rarest token
    intersection_docs = {} # INITIALIZED - NATH
    positions_doc = {}
    for p in sorted_search_postings_dict[first_token]: # looping thru all postings for rarest token (set of doc_id)
        intersection_docs[p["doc_ID"]] = calc_tfidf(
            p["freq"], len(sorted_search_postings_dict[first_token]), total_n, p["imp_freq"]
        ) # len(sorted_search_postings_dict[first_posting]) instead of len(p) - NATH
        
        if p["positions"]: # check if token has positions in that doc_id
            positions_doc[p["doc_ID"]] = {first_token: p["positions"]}        
    
    # boolean and with remaining token (except the first one)
    for token, p_list in list(sorted_search_postings_dict.items())[1:]:
        
        current = dict()
        for p in p_list:
            #current[p["doc_ID"]] = calc_tfidf(p["freq"], len(p_list), total_n, p["imp_freq"]) # len(p_list) instead len(p) - NATH
            current[p["doc_ID"]] = p # store the current posting
        update_intersection = dict()
        
        for docID in intersection_docs:
            if docID in current:
                p = current[docID]
                update_intersection[docID] = calc_tfidf(p["freq"], len(p_list), total_n, p["imp_freq"]) + intersection_docs[docID]
                
                # load positional_doc
                if p["positions"] and docID in positions_doc:
                    positions_doc[docID][token] = p["positions"]
                    
        intersection_docs = update_intersection
        # print(positions_doc) # contain positions of token in doc_id -> {11702: {'crista': [473], 'lope': [474]}, 11707: {'crista': [457, 496], 'lope': [458, 497, 533, 618]}, ...}
        # print(intersection_docs) # contains relevance scores of doc_id -> {11702: 4.939824580444155, 11707: 7.124329481906486, ...}
        # add positional boost to the score here
        for docID in intersection_docs:
           if docID in positions_doc:
              intersection_docs[docID] += calc_positional_boost(positions_doc[docID])
        #     #   print(calc_positional_boost(positions_doc[docID]))
    
    return intersection_docs
  
  
def calc_positional_boost(positions_of_tokens: dict) -> float:
    boost = 0.0
    all_tokens = list(positions_of_tokens.keys())
    n = len(all_tokens) # length of the query tokens
    consecutive_count = 0
    if n < 2:
        return 0.0 # single query
    
    beginning_pos = sorted(positions_of_tokens[all_tokens[0]])
    # 1. right next to each other (within 1 space)
    for begin in beginning_pos:
        found = True
        for i in range(1,n):
            expected = begin + i
            if expected not in positions_of_tokens[all_tokens[i]]:
                found = False
                break
        if found:
            consecutive_count += 1
    boost += float(consecutive_count)
    # if boost > 0: 
    #     print(boost)
    return boost * 5
 
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
    while True:
        print("\n-------------------------------------------------------------------------------------------------------")
        user_query = input("Please enter your query (type '-QUIT-' to quit): ")

        #method of timing found from: https://www.programiz.com/python-programming/examples/elapsed-time

        start = perf_counter()

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

        end = perf_counter()

        print(f"Time elapsed: {(end - start) * 1000} ms")
        print()



