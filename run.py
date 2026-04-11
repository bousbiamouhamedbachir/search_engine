import os
import subprocess
from app import create_app, db
from app.services.search_service import index_all_files

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Note: the old static file indexing logic is still here, but we now process new files in the background
        
    # Start the background indexer as a subprocess with module path
    indexer_process = subprocess.Popen(['python3', '-m', 'app.services.indexer_worker'])
    
    try:
        app.run(debug=True, port=5000, use_reloader=False) # Disable reloader so we don't spawn multiple workers
    finally:
        # Cleanup subprocess when Flask exits
        indexer_process.terminate()
