# SearchCore: Vector Search Engine

A modern information retrieval system built with Flask, implementing the **TF-IDF (Term Frequency-Inverse Document Frequency)** and **Vector Space Model** with **Cosine Similarity**.

## 🚀 Features
- **Vectorial Search**: High-precision search using mathematical vector space models.
- **TF-IDF Ranking**: Documents are ranked by relevance, not just keyword matching.
- **Dynamic Indexing**: Upload text, PDF, Word, Excel, and PowerPoint documents; they are automatically indexed.
- **GoFile Integration**: Optional cloud storage for uploaded documents.
- **Modern UI/UX**: Premium dark-mode interface with glassmorphism and smooth animations.

## 🛠️ Architecture
- **Core Engine**: Located in `app/services/core/engine.py`, handles all IR calculations independently.
- **Frontend**: Responsive HTML5/CSS3 templates with a focus on premium aesthetics.
- **Backend**: Flask-based RESTful services and SQLite database for metadata and inverted indexes.

## 📋 Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bousbiamouhamedbachir/search_engine.git
   cd search_engine
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Database**:
   ```bash
   # Run the application once to create the database and index files
   python run.py
   ```

4. **Index existing files**:
   ```bash
   flask --app run.py web index
   ```

## 🏃 Usage
Run the development server:
```bash
python run.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

## 📂 Project Structure
- `app/services/core/engine.py`: The heart of the information retrieval logic.
- `app/routes/web.py`: Web interface routes.
- `app/models.py`: Database models for Files, Words, and TF-IDF weights.
- `app/static/data/`: Local storage for indexed text documents.

## 🧠 Technical Analysis & Tradeoffs

### ⚖️ Complexity Tradeoffs
This engine implements a **Vector Space Model (VSM)**. While more advanced than simple Boolean retrieval, it remains a "bag-of-words" approach. It prioritizes simplicity and mathematical explainability over the semantic understanding provided by Transformer-based models (like BERT).

### 🎯 Retrieval Quality
- **Strengths**: Excellent for keyword-heavy queries and exact term matching.
- **Weaknesses**: Lacks **Semantic Search** capabilities. For example, a search for "canine" might not return a document containing only the word "dog" unless a synonym expansion layer is added.

### ⚡ Indexing Speed
- **Performance**: Indexing is $O(N \times M)$ where $N$ is the number of documents and $M$ is the average number of unique terms per document.
- **Bottleneck**: The primary bottleneck is the database I/O when updating the `Redundace` (inverted index) table. For massive datasets, a specialized engine like **Apache Lucene** would be more efficient.

### 💾 Memory Usage
- **Storage**: The `Redundace` table stores weights for every unique term-document pair. As the vocabulary and document count grow, this table can expand significantly.
- **Optimization**: We use SQLite, which is memory-efficient but lacks the distributed scaling of systems like **Elasticsearch**.

### 📉 Ranking Limitations
- **Cosine Similarity**: While mathematically sound, it doesn't account for document length as effectively as **BM25**.
- **Static Weights**: The engine does not currently incorporate "PageRank" style authority or user feedback loops (clicked results) into the ranking algorithm.

### 🔄 Alternatives
If you require production-grade performance for millions of documents, consider:
1. **Elasticsearch / Solr**: Industry standard for text search using BM25.
2. **FAISS / ChromaDB**: Optimized for high-dimensional vector embeddings and semantic search.
3. **Whoosh**: A pure-Python search library for smaller-scale projects.

## 📄 License
This project is for educational purposes. Feel free to modify and use it for your own IR experiments.
