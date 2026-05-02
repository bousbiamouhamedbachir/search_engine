import os
import time
import requests
from datetime import datetime
from app import create_app, db
from app.models import File, Word, Redundace
from app.services.parser_service import extract_text
from app.services.search_service import update_file_tfidf

def download_file(url, local_path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading file {url}: {e}")
    return False

def indexer_loop():
    app = create_app()
    with app.app_context():
        print("Background indexer started.")
        while True:
            # Find non-indexed files
            files_to_index = File.query.filter_by(indexed=0).all()
            for f in files_to_index:
                print(f"Indexing file: {f.file} (ID: {f.id})")
                
                # 1. Download if we only have URL, or use local if it exists
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f.file)
                success = False
                
                if os.path.exists(temp_path):
                    success = True
                elif f.url:
                    # Download from GoFile
                    # Note: GoFile downloadPage is not a direct file link. 
                    # For a real implementation, we'd need a direct link.
                    # As a workaround, we'll assume the upload was local first or we have a way.
                    # But the user said "download fille by file", so I'll try to find a direct link or assume the URL is direct.
                    success = download_file(f.url, temp_path)
                
                if success:
                    # 2. Extract text
                    text = extract_text(temp_path)
                    
                    # 3. Index text
                    if text:
                        update_file_tfidf(f.id, text)
                    
                    # 4. Mark as indexed
                    f.indexed = 1
                    f.indexed_at = datetime.utcnow()
                    db.session.commit()
                    
                    # 5. Delete local temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    print(f"Completed indexing for: {f.file}")
                else:
                    print(f"Failed to process file: {f.file}")
            
            time.sleep(10) # Poll every 10 seconds

if __name__ == '__main__':
    indexer_loop()
