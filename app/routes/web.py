from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
import os
from werkzeug.utils import secure_filename
from app.models import Search, Result, File
from app.services.search_service import vectorial_search, index_all_files
from app.services.gofile_service import upload_to_gofile
from app import db
from datetime import datetime

web_bp = Blueprint('web', __name__)

@web_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@web_bp.route('/search', methods=['POST'])
def search():
    query = request.form.get('query') or ''
    if not query:
        return redirect(url_for('web.index'))

    # Perform search (vectorial_search now handles Search/Result DB entries internally if desired, 
    # but we'll let it return results and we can display them)
    results = vectorial_search(query)
    
    return render_template('results.html', query=query, results=results)

@web_bp.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')

@web_bp.route('/upload-file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static/data')
        os.makedirs(upload_folder, exist_ok=True)
        local_path = os.path.join(upload_folder, filename)
        file.save(local_path)
        
        # Upload to GoFile (optional, depends on user preference)
        url = None
        try:
            url = upload_to_gofile(local_path)
        except:
            pass # Continue even if gofile fails
        
        # Save to DB
        new_file = File(
            file=filename,
            url=url,
            uploaded_at=datetime.utcnow(),
            indexed=0
        )
        db.session.add(new_file)
        db.session.commit()
        
        # Re-index files to include new one
        index_all_files()
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'message': 'File uploaded and indexed successfully'
        })
    return jsonify({'error': 'Upload failed'}), 500

@web_bp.route('/history')
def history():
    all_history = Search.query.order_by(Search.at.desc()).limit(50).all()
    return render_template('history.html', history=all_history)

@web_bp.route('/view/<int:file_id>')
def view_file(file_id):
    file_obj = File.query.get_or_404(file_id)
    # If it's a gofile link, redirect there, otherwise serve locally
    if file_obj.url:
        return redirect(file_obj.url)
    return redirect(url_for('static', filename=f'data/{file_obj.file}'))

@web_bp.cli.command('index')
def index_command():
    index_all_files()
    print("Files indexed successfully.")
