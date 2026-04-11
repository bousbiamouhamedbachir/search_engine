from flask import Blueprint, render_template, request, jsonify, redirect, current_app
import os
from werkzeug.utils import secure_filename
from app.models import Search, Result, File
from app.services.search_service import vectorial_search, index_all_files
from app.services.gofile_service import upload_to_gofile
from app import db
from datetime import datetime

web_bp = Blueprint('web', __name__)

@web_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        json_data = request.get_json(silent=True) or {}
        query = request.form.get('query') or json_data.get('query') or ''
        page = request.args.get('page', 1, type=int)
        per_page = 10
        json_mode = request.args.get('json', '0') == '1' or json_data.get('json') == 1

        if not query:
            if json_mode:
                return jsonify({'error': 'No query provided'}), 400
            return render_template('index.html', error='Please enter a search query.')

        # Record search
        new_search = Search(query=query, at=datetime.utcnow())
        db.session.add(new_search)
        db.session.commit()

        # Perform search
        search_results = vectorial_search(query)
        
        # Save results to db and collect with IDs
        paginated_results_data = []
        full_results_list = []
        
        for file_id, score in search_results:
            res = Result(search=new_search.id, file=file_id, score=score)
            db.session.add(res)
            full_results_list.append(res)
        
        db.session.commit()

        # Pagination logic
        total = len(search_results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_res_objects = full_results_list[start:end]
        
        # Hydrate results with file info and result ID
        final_results = []
        for res_obj in paginated_res_objects:
            file_obj = File.query.get(res_obj.file)
            final_results.append({
                'result_id': res_obj.id,
                'filename': file_obj.file,
                'score': round(res_obj.score, 4),
                'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d')
            })

        if json_mode:
            return jsonify({
                'query': query,
                'total': total,
                'page': page,
                'results': final_results
            })

        return render_template('results.html', 
                               query=query, 
                               results=final_results, 
                               total=total, 
                               page=page, 
                               pages=(total // per_page) + (1 if total % per_page > 0 else 0))

    return render_template('index.html')

@web_bp.route('/filee')
def view_file():
    result_id = request.args.get('id', type=int)
    if not result_id:
        return "Missing result ID", 400
    
    result = Result.query.get_or_404(result_id)
    result.clicked = 1
    db.session.commit()
    
    file_obj = File.query.get(result.file)
    if file_obj.url:
        return redirect(file_obj.url)
    return redirect(f'/static/data/{file_obj.file}')

@web_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.getcwd(), 'app/static/data')
        os.makedirs(upload_folder, exist_ok=True)
        local_path = os.path.join(upload_folder, filename)
        file.save(local_path)
        
        # Upload to GoFile
        url = upload_to_gofile(local_path)
        
        # Save to DB
        new_file = File(
            file=filename,
            url=url,
            uploaded_at=datetime.utcnow(),
            indexed=0
        )
        db.session.add(new_file)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'url': url,
            'message': 'File uploaded and queued for indexing'
        })
    return jsonify({'error': 'Upload failed'}), 500

@web_bp.route('/click/<int:search_id>/<int:file_id>', methods=['POST'])
def track_click(search_id, file_id):
    result = Result.query.filter_by(search=search_id, file=file_id).first()
    if result:
        result.clicked = 1
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 404

@web_bp.cli.command('index')
def index_command():
    index_all_files()
    print("Files indexed successfully.")
