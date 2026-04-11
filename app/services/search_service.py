import os
import re
import math
from datetime import datetime
from app import db
from app.models import File, Word, Redundace

def tokenize(text):
    return re.findall(r'\w+', text.lower())

def index_all_files():
    static_folder = 'app/static/data'
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
        return

    files_on_disk = [f for f in os.listdir(static_folder) if f.endswith('.txt')]
    for filename in files_on_disk:
        file_path = os.path.join(static_folder, filename)
        existing_file = File.query.filter_by(file=filename).first()
        
        # Simple logic: if file exists, skip it, or update it
        if not existing_file:
            new_file = File(file=filename, uploaded_at=datetime.utcnow(), indexed_at=datetime.utcnow())
            db.session.add(new_file)
            db.session.commit()
            existing_file = new_file

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
                tokens = tokenize(content)
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

    # 3. Calculate IDF for each word
    word_idf = {} # {word_id: idf}
    for word_str, word_id in word_map.items():
        docs_with_word = sum(1 for file_id in file_frequencies if word_str in file_frequencies[file_id])
        word_idf[word_id] = math.log10(num_docs / docs_with_word)

    # 4. Calculate Weight (TF * IDF) and save to Redundace
    # Clear old Redundace weights first for simplicity
    Redundace.query.delete()
    
    for file_id, freqs in file_frequencies.items():
        total_tokens = sum(freqs.values())
        for word_str, count in freqs.items():
            word_id = word_map[word_str]
            tf = count / total_tokens
            weight = tf * word_idf[word_id]
            redundace = Redundace(word=word_id, file=file_id, wheight=weight)
            db.session.add(redundace)
    
    db.session.commit()

def vectorial_search(query):
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    # Get query vector (TF only for query, or TF-IDF if we have access to IDF)
    query_freqs = {}
    for t in query_tokens:
        query_freqs[t] = query_freqs.get(t, 0) + 1
    
    total_q_tokens = sum(query_freqs.values())
    
    # We need IDF for query words too
    results = []
    
    # Get all candidate files that have at least one query word
    candidate_files = db.session.query(File.id).join(Redundace).join(Word).filter(Word.word.in_(query_tokens)).distinct().all()
    candidate_file_ids = [f[0] for f in candidate_files]
    
    if not candidate_file_ids:
        return []

    scores = {} # {file_id: score}
    
    for file_id in candidate_file_ids:
        # Cosine Similarity = (Dot Product(A, B)) / (Norm(A) * Norm(B))
        # A = query vector, B = document vector
        
        dot_product = 0
        norm_a = 0
        norm_b = 0
        
        # Get doc weights for this file
        # Cosine Similarity = (Dot Product(A, B)) / (Norm(A) * Norm(B))
        
        dot_product = 0
        norm_a = 0
        norm_b = 0
        
        # Get doc weights for this file
        redundances = Redundace.query.filter_by(file=file_id).all()
        doc_weights = {r.word_obj.word: r.wheight for r in redundances}
        
        # Query weights (TF-IDF)
        for q_word, q_count in query_freqs.items():
            word_obj = Word.query.filter_by(word=q_word).first()
            if word_obj:
                # Use IDF from db if available
                docs_with_word = Redundace.query.filter_by(word=word_obj.id).count()
                num_docs = File.query.count()
                idf = math.log10(num_docs / docs_with_word) if docs_with_word > 0 else 0
                
                q_weight = (q_count / total_q_tokens) * idf
                dot_product += q_weight * doc_weights.get(q_word, 0)
                norm_a += q_weight ** 2
        
        for w in doc_weights.values():
            norm_b += w ** 2
            
        if norm_a > 0 and norm_b > 0:
            scores[file_id] = dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))
        else:
            scores[file_id] = 0

    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results

def update_file_tfidf(file_id, text):
    tokens = tokenize(text)
    if not tokens:
        return

    # Word frequencies in this file
    freqs = {}
    for t in tokens:
        freqs[t] = freqs.get(t, 0) + 1
    
    total_tokens = sum(freqs.values())
    
    # Pre-fetch existing words to avoid querying inside loop
    existing_words = Word.query.filter(Word.word.in_(freqs.keys())).all()
    word_map = {w.word: w for w in existing_words}
    
    # Add missing words
    new_words = []
    for word_str in freqs.keys():
        if word_str not in word_map:
            new_w = Word(word=word_str)
            db.session.add(new_w)
            new_words.append(new_w)
            word_map[word_str] = new_w
            
    if new_words:
        db.session.commit() # Commit once to obtain IDs for new words
    
    # Calculate TF*IDF and save Redundace
    num_docs = File.query.count()
    if num_docs == 0: num_docs = 1

    for word_str, count in freqs.items():
        word_obj = word_map[word_str]
        
        # Calculate IDF (simple approximation if indexing one by one)
        docs_with_word = Redundace.query.filter_by(word=word_obj.id).count()
        if docs_with_word == 0: docs_with_word = 1
        idf = math.log10(num_docs / docs_with_word)
        
        weight = (count / total_tokens) * idf
        
        # Save to Redundace
        redundace = Redundace.query.filter_by(word=word_obj.id, file=file_id).first()
        if redundace:
            redundace.wheight = weight
        else:
            redundace = Redundace(word=word_obj.id, file=file_id, wheight=weight)
            db.session.add(redundace)
            
    db.session.commit() # Final commit for all redundance weights
