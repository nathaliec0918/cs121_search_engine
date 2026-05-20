import json
import sys
import os
from pathlib import Path
import re
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from math import log


'''
Posting structure {
    docID
    frequency_count (tfidf)
    fields
    positions?
}

Report structure (json) {
    num_indexed_doc: int()
    num_unique_tokens: int()
    index_size: int()
    indexed_doc: {"docID": 0, "token": ""}
    unique_tokens: defaultdict()
}
'''

STEMMER = PorterStemmer()
PARTIAL_DIR = "partial_indexes"


class Posting:
    def __init__(self, docID, frequencies, fields = None, positions = None):
        self.docID = docID
        self.frequencies = frequencies
        #self.fields = fields for future assignments
        #self.positions = positions

# partial index flow 
def build_index(frontier: list) -> int:
    # basic flow
    index = dict()
    docIDIndex = dict()
    docID = 0
    batch_name = 0
    batch = []

    while frontier:
        batch_name += 1
        batch = get_batch(frontier, 100)
        for document in batch:
            if document.endswith(".json"):
                docID += 1
                
                unique_stemmed_tokens = set()
                unique_stemmed_tokens, frequencies, url = parse_to_token(document) #stemmed_tokens is already duplicate removed
                docIDIndex[docID] = url
                for t in unique_stemmed_tokens:
                    if t not in index:
                        index[t] = []
                    index[t].append(Posting(docID, frequencies[t]))

            else:
                continue
                #print(document) #REMOVE LATER
        
        # update on batch level
        with open("doc_id_to_url.json", "w", encoding="utf-8") as file:
            json.dump(docIDIndex, file)

        write_new_report(num_docs_seen = docID, potential_new_tokens = index.keys())
        
        # store then reset batch
        sort_and_write_to_disk(index, batch_name) # uploading too Disk, reset RAM
        index = dict()

        return docID
    
    merge_partials()
        
    return


def write_new_report(num_docs_seen = None, potential_new_tokens = None, index_size = None):
    with open("a3_1_report.json", "r", encoding="utf-8") as file:
        try:
            report = json.load(file)
        except json.decoder.JSONDecodeError:
            report = {"num_indexed_docs": 0,
                    "num_unique_tokens": 0,
                    "total_size_kb": 0,
                    "unique_tokens": list(), #set
                }
            
    if num_docs_seen:
        report["num_indexed_docs"] = num_docs_seen
    if potential_new_tokens:
        report["unique_tokens"] = list(set(report["unique_tokens"] + list(potential_new_tokens)))
        report["num_unique_tokens"] = len(report["unique_tokens"])
    if index_size:
        report["total_size_kb"] += index_size

    with open("a3_1_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f)


def get_batch(frontier: list, batch_size: int)->list :
    #returns batch of first n urls and removes them from the frontier
    if batch_size >= len(frontier):
        batch_size = len(frontier)
    batch = frontier[:batch_size] 
    del frontier[:batch_size]

    return batch


def sort_and_write_to_disk(index: dict, name: int):
    os.makedirs(PARTIAL_DIR, exist_ok=True)
    path = os.path.join(PARTIAL_DIR, f"partial_{name}.json")

    postings_as_dict = {}
    for token in index:
        posting_list = []
        for p in index[token]:
            posting_list.append({"doc_ID": p.docID, "freq": p.frequencies})
        postings_as_dict[token] = posting_list

    with open(path, "w", encoding="utf-8") as f:
        json.dump(postings_as_dict, f)
        
    file_size_kilobytes = os.path.getsize(path) / 1024
    write_new_report(index_size = file_size_kilobytes)
    

def parse_to_token(file: json) -> list[str]:
    # json structure: {"url":"", "content":""}
    try: 
        with open(file, "r", encoding="utf-8") as f:
            document = json.load(f) # hht
        try: 
            soup = BeautifulSoup(document["content"], "xml")
        except:
            soup = BeautifulSoup(document["content"], "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text_content = soup.get_text(separator=" ")
        tokens = re.findall(r"[a-zA-Z0-9]+", text_content.lower())

        # porter stemmer
        stemmed = [STEMMER.stem(token) for token in tokens]

        # frequencies
        word_frequencies = dict()
    
        for word in stemmed:
            if word in word_frequencies:
                word_frequencies[word] += 1
            else: 
                word_frequencies[word] = 1

        doc_url = document["url"]

        return set(stemmed), word_frequencies, doc_url
    
        
    except (json.JSONDecodeError, OSError):
        return set(), {}, ""


def get_corpus(top, corpus: list):
    for dirpath, dirnames, filenames in os.walk(top):
        for name in filenames:
            corpus.append(os.path.join(dirpath, name))


def clear_previous_index():
    if os.path.exists(PARTIAL_DIR):
        for file in os.listdir(PARTIAL_DIR):
            os.remove(os.path.join(PARTIAL_DIR, file))

    with open("a3_1_report.json", "w", encoding="utf-8"):
        pass

def merge_partials():
    merged = {}
    for file in os.listdir(PARTIAL_DIR):
        path = os.path.join(PARTIAL_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            partial = json.load(f)
        for token, postings, in partial.items():
            if token not in merged:
                merged[token] = []
            merged[token].extend(postings)

    with open("final_index.json", "w", encoding="utf-8") as f:
        json.dump(merged, f)
    
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
    sorted_search_postings_dict = dict(sorted(search_postings_dict.items(), key=lambda x: len(x[1])))
    # get only shortest p list to compare
    first_token = next(iter(sorted_search_postings_dict))
    for p in sorted_search_postings_dict[first_token]:
        intersection_docs[p["doc_ID"]] = calc_tfidf(p["freq"], len(p), total_n)
    
    # boolean and
    for token, p_list in list(sorted_search_postings_dict.items())[1:]:
        
        current = dict()
        for p in p_list:
            current[p["doc_ID"]] = calc_tfidf(p["freq"], len(p), total_n)
        
        update_intersection = dict()
        for docID in intersection_docs:
            if docID in current:
                update_intersection[docID] = current[docID] + intersection_docs[docID]
        intersection_docs = update_intersection
    
    return intersection_docs
   
def rank_frequencies(intersection_docs: dict): # imp tf-idf here?
    result = sorted(intersection_docs.items(), key=lambda x: -x[1])

    to_show = 5 if len(result) >= 5 else len(result)
    return result[:to_show]

def get_URLs_from_doc(top5docs: dict) -> dict: 
    asURL = {}
    with open("doc_id_to_url.json", "r", encoding="utf-8") as file:
        idIndex = json.load(file)
    
    for doc, score in enumerate(top5docs):
        asURL[int(idIndex[str(doc)])] = score # .json's always store keys as strings

    return asURL

def print_URLs_and_scores(url_dict: dict) -> None:
    if not url_dict:
        print("No results found.\n")
        return

    n = 1
    print(f"Top {len(url_dict)} Results:")
    for url, score in enumerate(url_dict):
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
    full_search = search(query_as_tokens, total_n_docs)
    if full_search:
        boolean_search = get_intersection(full_search, total_n_docs)
        top5_docID = rank_frequencies(boolean_search)
    top5_URL = get_URLs_from_doc(top5_docID)
    print_URLs_and_scores(top5_URL)
    query(total_n_docs)
    

def main():
    if len(sys.argv) == 2:
        filePath = sys.argv[1]
        clear_previous_index()
        try:
            corpus = []
            get_corpus(filePath, corpus)
            #print(len(corpus))
            total_n_docs = build_index(corpus) # also get docID associated URLs (loaded in json)
            query(total_n_docs)
        except:
            print("Unable to open path or path is invalid. Please restart the program to try again.") # CHANGE LATER
        
        
    else:
        print("Please restart the program and specify one file path") 


if __name__ == "__main__":
    main()
    #  if len(sys.argv) == 2:
    #     filePath = sys.argv[1]
    #     clear_previous_index()
    #     corpus = []
    #     get_corpus(filePath, corpus)
    #     print(len(corpus))
    