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

    with open("final_index.json", "w", encoding="utf-8") as f:
        json.dump(merged, f)


def get_existing_pi_dir() -> tuple:
    existing_pi_dir = input("Please enter the root path of your partial indexes.\n(type '-QUIT-' to quit)").strip()
    if existing_pi_dir == "-QUIT-":
        return "", 0
    if not os.path.isdir(existing_pi_dir):
        print("Path given is not a valid directory")
        get_existing_pi_dir()
    else:
        try:
            test_file = os.listdir(existing_pi_dir)[0]
            path = os.path.join(existing_pi_dir, test_file)
            with open(path, "r", encoding="utf-8") as f:
                partial = json.load(f)
            first_post = list(partial.values())[0][0] #first [0] gets the first posting list, sec [0] gets first {docid, freq} in that list
            
            assert set(first_post.keys()) == {"doc_ID", "freq"}

            len_corpus = int(input("Please enter how many documents are in the corpus.").strip())
            
            return existing_pi_dir, len_corpus

        except json.JSONDecodeError as je:
            print("Directory does not contain json files. Please use the indexer.")
            get_existing_pi_dir()
        except AssertionError as ae:
            print("Partial Index postings do not match expected structure: docid, freq")
            get_existing_pi_dir()
        except ValueError:
            print("Invalid length of corpus.")
            get_existing_pi_dir()

    return existing_pi_dir


def create_new_index() -> int:
    filePath = input("Please give root of the directory to index")
    indexer.clear_previous_index()
    corpus = []
    indexer.get_corpus(filePath, corpus)
    #print(len(corpus))
    total_n_docs = indexer.build_index(corpus) # also get docID associated URLs (loaded in json)
    return total_n_docs


def main():
    index_exists = input("Welcome. Do you already have your Index Built? (Please enter 'Y' or 'N')\n(type '-QUIT-' to quit)")
    if index_exists == "-QUIT-":
        return
    index_exists = index_exists.strip().lower()
    if index_exists == "y":
        existing_pir_dir, total_n_docs = get_existing_pi_dir()
        if not existing_pir_dir:
            return
        merge_partials(existing_pir_dir)
        search.query(total_n_docs)
        
    elif index_exists == 'n':
        total_n_docs = create_new_index()
        merge_partials(PARTIAL_DIR)
        search.query(total_n_docs)
        
    
    else:
        main()

if __name__ == "__main__":
    main()
    #  if len(sys.argv) == 2:
    #     filePath = sys.argv[1]
    #     clear_previous_index()
    #     corpus = []
    #     get_corpus(filePath, corpus)
    #     print(len(corpus))
    