import json
import sys

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

class Posting:
    def __init__(self, docID, freq_count, fields):
        self.docID = docID
        self.freq_count = freq_count
        self.fields = fields

# general flow
def build_index(corpus:set):
    # basic flow
    index = dict()
    docID = 0
    for document in corpus:
        docID += 1
        parsed_doc = parser(document)
        token = tokenize(parsed_doc)
        unique_token = set(list(token)) # remove duplicates
        for t in unique_token:
            if index[t] not in index:
                index[t] = []
            index[t].append(Posting(docID))
    
    return index

def parser(document:json) -> list:
    with open(document, "r", encoding="utf-8") as file:
        try:
            parsed = json.load(file)
        except json.decoder.JSONDecodeError:
            parsed = {
                "num_indexed_doc": 0,
                "num_unique_tokens": 0,
                "index_size": 0,
                "indexed_doc": {"docID": 0, "token": ""},
                "unique_tokens": dict()
            }
    return parsed 

def tokenize(parsed_doc):
    # nltk
    pass    


if __name__ == "__main__":

    pass


