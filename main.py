import indexer
import search
import os
import json
from indexer import PARTIAL_DIR

def merge_partials(partial_dir: str):
    merged = {}
    for file in os.listdir(partial_dir):
        path = os.path.join(partial_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            partial = json.load(f)
        for token, postings, in partial.items():
            if token not in merged:
                merged[token] = []
            merged[token].extend(postings)

    seek_table = {}
    with open("final_index.json", "w", encoding="utf-8") as f:
        for token, postings in sorted(merged.items()):
            offset = f.tell() # byte position before writing this line
            seek_table[token] = offset
            f.write(json.dumps({token: postings}) + "\n")

    with open("seek_table.json", "w", encoding="utf-8") as f:
        json.dump(seek_table, f)

def confirm_existing_index() -> tuple:
    if not os.path.isfile("final_index.json"):
        print("Index does not exist. Please build one.")
        return "", 0
    else:
        try:
            with open("final_index.json", "r", encoding="utf-8") as f:
                index = json.load(f)
            first_post = list(index.values())[0][0] #first [0] gets the first posting list, sec [0] gets first {docid, freq} in that list
            
            assert set(first_post.keys()) == {"doc_ID", "freq", "imp_freq"}

            len_corpus = int(input("\nPlease enter how many documents are in the corpus: ").strip())
            if len_corpus < 0:
                raise ValueError
            
            return "final_index.json", len_corpus

        except json.JSONDecodeError as je:
            print("File is not a json. Please use the indexer.")
            return "", 0
        except AssertionError as ae:
            print("Index postings do not match expected structure: docid, freq, imp_freq.")
            return "", 0
        except ValueError:
            print("Invalid length of corpus.")
            return "", 0


def create_new_index() -> int:
    filePath = input("\nPlease give root of the directory to index: ")
    indexer.clear_previous_index()
    corpus = []
    indexer.get_corpus(filePath, corpus)
    #print(len(corpus))
    total_n_docs = indexer.build_index(corpus) # also get docID associated URLs (loaded in json)
    return total_n_docs


def main():
    while True:
        print("\n=======================================================================================================")
        index_exists = input("Welcome. Do you already have your Index Built? (Please enter 'Y' or 'N')\n(type '-QUIT-' to quit): ")
        if index_exists == "-QUIT-":
            return
        index_exists = index_exists.strip().lower()
        if index_exists == "y":
            index_path, total_n_docs = confirm_existing_index()
            if not index_path:
                return
            search.query(total_n_docs)
            
        elif index_exists == 'n':
            total_n_docs = create_new_index()
            merge_partials(PARTIAL_DIR)
            search.query(total_n_docs)

if __name__ == "__main__":
    main()
    #  if len(sys.argv) == 2:
    #     filePath = sys.argv[1]
    #     clear_previous_index()
    #     corpus = []
    #     get_corpus(filePath, corpus)
    #     print(len(corpus))
    