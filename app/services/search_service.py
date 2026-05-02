import os
import math
from datetime import datetime
from app import db
from app.models import File, Word, Redundace, Search, Result
from app.services.core.engine import SearchEngine

engine = SearchEngine()

def index_all_files():
    static_folder = 'app/static/data'
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
        return

    supported_extensions = ('.txt', '.pdf', '.docx', '.xlsx', '.pptx')
    files_on_disk = [f for f in os.listdir(static_folder) if f.lower().endswith(supported_extensions)]
    for filename in files_on_disk:
        existing_file = File.query.filter_by(file=filename).first()
        if not existing_file:
            new_file = File(file=filename, uploaded_at=datetime.utcnow(), indexed_at=datetime.utcnow())
            db.session.add(new_file)
            db.session.commit()

    # Now calculate TF-IDF for all files
    all_files = File.query.all()
    num_docs = len(all_files)
    if num_docs == 0:
        return

    # 1. Get frequencies for each file
    file_frequencies = {} # {file_id: {word: count}}
    all_words_found = set()
    
    for f in all_files:
        file_path = os.path.join('app/static/data', f.file)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                tokens = engine.tokenize(content)
                freqs = {}
                for t in tokens:
                    freqs[t] = freqs.get(t, 0) + 1
                    all_words_found.add(t)
                file_frequencies[f.id] = freqs

    # 2. Get/Create all words in db
    word_map = {} # {word_str: word_id}
    for word_str in all_words_found:
        word_obj = Word.query.filter_by(word=word_str).first()
        if not word_obj:
            word_obj = Word(word=word_str)
            db.session.add(word_obj)
            db.session.commit()
        word_map[word_str] = word_obj.id

    # 3. Calculate Weight (TF * IDF) and save to Redundace
    Redundace.query.delete()
    
    for file_id, freqs in file_frequencies.items():
        total_tokens = sum(freqs.values())
        for word_str, count in freqs.items():
            word_id = word_map[word_str]
            
            # Calculate IDF
            docs_with_word = sum(1 for fid in file_frequencies if word_str in file_frequencies[fid])
            idf = engine.calculate_idf(num_docs, docs_with_word)
            
            tf = count / total_tokens
            weight = tf * idf
            
            redundace = Redundace(word=word_id, file=file_id, wheight=weight)
            db.session.add(redundace)
    
    db.session.commit()

def vectorial_search(query_text):
    query_tokens = engine.tokenize(query_text)
    if not query_tokens:
        return []

    # Store search history
    new_search = Search(query=query_text)
    db.session.add(new_search)
    db.session.commit()

    num_docs = File.query.count()
    
    def get_word_idf(word_str):
        word_obj = Word.query.filter_by(word=word_str).first()
        if not word_obj:
            return 0
        docs_with_word = Redundace.query.filter_by(word=word_obj.id).count()
        return engine.calculate_idf(num_docs, docs_with_word)

    # Calculate query vector
    query_vector = engine.get_query_vector(query_text, get_word_idf)
    
    # Get all candidate files (files that share at least one word with the query)
    candidate_files = db.session.query(File).join(Redundace).join(Word).filter(Word.word.in_(query_tokens)).distinct().all()
    
    results = []
    for file_obj in candidate_files:
        # Get doc vector
        redundances = Redundace.query.filter_by(file=file_obj.id).all()
        doc_vector = {r.word_obj.word: r.wheight for r in redundances}
        
        score = engine.calculate_cosine_similarity(query_vector, doc_vector)
        if score > 0:
            results.append((file_obj, score))
            # Save result to DB
            db_result = Result(search=new_search.id, file=file_obj.id, score=score)
            db.session.add(db_result)

    db.session.commit()
    
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def update_file_tfidf(file_id, text):
    """Update TF-IDF for a single file (usually after upload)."""
    tokens = engine.tokenize(text)
    if not tokens:
        return

    tf_map = engine.calculate_tf(tokens)
    num_docs = File.query.count()
    
    for word_str, tf in tf_map.items():
        word_obj = Word.query.filter_by(word=word_str).first()
        if not word_obj:
            word_obj = Word(word=word_str)
            db.session.add(word_obj)
            db.session.commit()
            
        docs_with_word = Redundace.query.filter_by(word=word_obj.id).count()
        if docs_with_word == 0: docs_with_word = 1 # Approximation
        
        idf = engine.calculate_idf(num_docs, docs_with_word)
        weight = tf * idf
        
        redundace = Redundace.query.filter_by(word=word_obj.id, file=file_id).first()
        if redundace:
            redundace.wheight = weight
        else:
            redundace = Redundace(word=word_obj.id, file=file_id, wheight=weight)
            db.session.add(redundace)
            
    db.session.commit()
