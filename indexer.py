import json
import sys
import os
from pathlib import Path
import re
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer


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
def build_index(frontier: list):
    # basic flow
    index = dict()
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
                unique_stemmed_tokens, frequencies = parse_to_token(document) #stemmed_tokens is already duplicate removed
                for t in unique_stemmed_tokens:
                    if t not in index:
                        index[t] = []
                    index[t].append(Posting(docID, frequencies[t]))

            else:
                continue
                #print(document) #REMOVE LATER
        
        # update on batch level
        write_new_report(num_docs_seen = docID, potential_new_tokens = index.keys())
        
        # store then reset batch
        sort_and_write_to_disk(index, batch_name) # uploading too Disk, reset RAM
        index = dict()
        
    return index


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

        return set(stemmed), word_frequencies
    
        
    except (json.JSONDecodeError, OSError):
        return set(), {}


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
    

def main():
    if len(sys.argv) == 2:
        filePath = sys.argv[1]
        clear_previous_index()
        try:
            corpus = []
            get_corpus(filePath, corpus)
            #print(len(corpus))
        except:
            print("Unable to open path or path is invalid. Please restart the program to try again.") # CHANGE LATER
        build_index(corpus)
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
    