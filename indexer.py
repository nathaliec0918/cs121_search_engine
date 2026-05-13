import json
import sys
import os.path
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
    batch = []
    while frontier:
        batch = get_batch(frontier, 100)
        for document in batch:
            docID += 1
            unique_stemmed_tokens, frequencies = parse_to_token(document) #stemmed_tokens is already duplicate removed
            for t in unique_stemmed_tokens:
                if t not in index:
                    index[t] = []
                index[t].append(Posting(docID, frequencies[t]))
        
        sort_and_write_to_disk(index, name) # uploading too Disk, reset RAM
        index = dict()
        
    return index

def get_batch(frontier: list, batch_size: int)->list :
    #returns batch of first n urls and removes them from the frontier
    batch = frontier[:batch_size]
    frontier = frontier[batch_size:]
    return batch


def sort_and_write_to_disk(index, name):
    ...

def parse_to_token(file: json) -> list[str]:
    # json structure: {"url":"", "content":""}
    try: 
        with open(file, "r", encoding="utf-8") as f:
            document = json.load(f) # hht
        try: 
            soup = BeautifulSoup(document["content"], "lxml")
        except:
            soup = BeautifulSoup(document["content"], "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text_content = soup.get_text(separator=" ")
        tokens = re.findall(r"[a-zA-Z]", text_content.lower())

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
        return []
    



# def report(document:json) -> list:
#     with open(document, "r", encoding="utf-8") as file:
#         try:
#             parsed = json.load(file)
#         except json.decoder.JSONDecodeError:
#             parsed = {
#                 "num_indexed_doc": 0,
#                 "num_unique_tokens": 0,
#                 "index_size": 0,
#                 "indexed_doc": {"docID": 0, "token": ""},
#                 "unique_tokens": dict()
#             }
#     return parsed

def get_corpus(top, corpus: list):
    for dirpath, dirnames, filenames in os.walk(top):
        for name in filenames:
            corpus.append(os.path.join(dirpath, name))

def tokenize(parsed_doc):
    # beautiful soup
    # json: {"url":"", "content":""}
    
    pass   

def main():
    if len(sys.argv) == 2:
        filePath = sys.argv[1]
        try:
            corpus = []
            get_corpus(filePath, corpus)
            build_index(corpus)
        
        except:
            print("Unable to open path or path is invalid. Please restart the program to try again.") # CHANGE LATER
    else:
        print("Please restart the program and specify one file path") 


if __name__ == "__main__":
    main()