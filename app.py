from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file, session
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import json

app = Flask(__name__)
app.secret_key = 'pdf-merger-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store merge history in memory (use database in production)
merge_history = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def get_pdf_info(filepath):
    try:
        reader = PdfReader(filepath, strict=False)
        return {
            'pages': len(reader.pages),
            'size': os.path.getsize(filepath)
        }
    except Exception as e:
        print(f"DEBUG: PDF info error for {filepath}: {str(e)}")
        return {'pages': 0, 'size': 0}

@app.route('/')
def index():
    """Home page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        print("DEBUG: Upload request received")
        print(f"DEBUG: Request files: {list(request.files.keys())}")
        print(f"DEBUG: Request form: {dict(request.form)}")
        
        if 'files' not in request.files:
            print("DEBUG: No 'files' key in request.files")
            flash('No files selected', 'error')
            return redirect(url_for('index'))
        
        files = request.files.getlist('files')
        print(f"DEBUG: Found {len(files)} files")
        
        if not files or files[0].filename == '':
            print("DEBUG: No files or empty filename")
            flash('No files selected', 'error')
            return redirect(url_for('index'))
        
        # Create session ID for this upload
        session_id = str(uuid.uuid4())
        session['upload_id'] = session_id
        session['merge_order'] = request.form.get('merge_order', 'filename')
        session['output_name'] = request.form.get('output_name', 'merged.pdf')
        
        print(f"DEBUG: Session ID: {session_id}")
        
        # Create session folder
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)
        print(f"DEBUG: Created session folder: {session_folder}")
        
        uploaded_files = []
        for i, file in enumerate(files):
            print(f"DEBUG: Processing file {i+1}: {file.filename}")
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(session_folder, filename)
                file.save(filepath)
                print(f"DEBUG: Saved file: {filepath}")
                
                # Validate and get PDF info
                pdf_info = get_pdf_info(filepath)
                
                # Skip corrupted PDFs
                if pdf_info['pages'] == 0:
                    print(f"DEBUG: Skipping corrupted PDF: {filename}")
                    os.remove(filepath)  # Remove corrupted file
                    continue
                
                uploaded_files.append({
                    'name': filename,
                    'path': filepath,
                    'pages': pdf_info['pages'],
                    'size': f"{pdf_info['size'] / 1024:.1f} KB"
                })
                print(f"DEBUG: File info - Pages: {pdf_info['pages']}, Size: {pdf_info['size']} bytes")
            else:
                print(f"DEBUG: Skipped invalid file: {file.filename if file else 'None'}")
        
        if not uploaded_files:
            print("DEBUG: No valid PDF files uploaded")
            flash('No valid PDF files uploaded. Please select PDF files only.', 'error')
            return redirect(url_for('index'))
        
        session['uploaded_files'] = uploaded_files
        print(f"DEBUG: Stored {len(uploaded_files)} files in session")
        flash(f'{len(uploaded_files)} PDF files uploaded successfully!', 'success')
        return redirect(url_for('merge'))
        
    except Exception as e:
        print(f"DEBUG: Upload failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/merge')
def merge():
    """Show merge options page"""
    print(f"DEBUG: Session keys: {list(session.keys())}")
    print(f"DEBUG: Session upload_id: {session.get('upload_id', 'None')}")
    
    if 'uploaded_files' not in session:
        print("DEBUG: No uploaded_files in session, checking for existing uploads...")
        
        # Try to recover from existing uploads directory
        upload_id = session.get('upload_id')
        if upload_id:
            session_folder = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
            if os.path.exists(session_folder):
                print(f"DEBUG: Found existing session folder: {session_folder}")
                # Rebuild file list from directory
                uploaded_files = []
                for filename in os.listdir(session_folder):
                    if filename.endswith('.pdf'):
                        filepath = os.path.join(session_folder, filename)
                        pdf_info = get_pdf_info(filepath)
                        uploaded_files.append({
                            'name': filename,
                            'path': filepath,
                            'pages': pdf_info['pages'],
                            'size': f"{pdf_info['size'] / 1024:.1f} KB"
                        })
                
                if uploaded_files:
                    session['uploaded_files'] = uploaded_files
                    print(f"DEBUG: Recovered {len(uploaded_files)} files from session folder")
                else:
                    flash('No files uploaded. Please upload files first.', 'error')
                    return redirect(url_for('index'))
            else:
                flash('No files uploaded. Please upload files first.', 'error')
                return redirect(url_for('index'))
        else:
            flash('No files uploaded. Please upload files first.', 'error')
            return redirect(url_for('index'))
    
    files = session['uploaded_files']
    print(f"DEBUG: Found {len(files)} files in session")
    
    # Sort files based on merge order
    merge_order = session.get('merge_order', 'filename')
    if merge_order == 'filename':
        files.sort(key=lambda x: x['name'])
    elif merge_order == 'upload_order':
        pass  # Keep original order
    
    return render_template('simple_merge.html', files=files, file_count=len(files))

@app.route('/reorder', methods=['POST'])
def reorder_files():
    """Handle file reordering"""
    try:
        data = request.get_json()
        new_order = data.get('order', [])
        
        if 'uploaded_files' not in session:
            return jsonify({'status': 'error', 'message': 'No files in session'})
        
        files = session['uploaded_files']
        reordered_files = []
        
        # Reorder files based on the new order
        for filename in new_order:
            for file_info in files:
                if file_info['name'] == filename:
                    reordered_files.append(file_info)
                    break
        
        # Update session with new order
        session['uploaded_files'] = reordered_files
        print(f"DEBUG: Reordered files: {[f['name'] for f in reordered_files]}")
        
        return jsonify({'status': 'success', 'message': 'Files reordered'})
        
    except Exception as e:
        print(f"DEBUG: Reorder failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/process', methods=['POST'])
def process_merge():
    """Process PDF merge request"""
    try:
        print("DEBUG: Starting merge process")
        if 'uploaded_files' not in session:
            flash('No files to merge', 'error')
            return redirect(url_for('index'))
        
        files = session['uploaded_files']
        print(f"DEBUG: Merging {len(files)} files")
        output_filename = request.form.get('output_filename', 'merged_document.pdf')
        
        # Ensure output filename ends with .pdf
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
        
        print(f"DEBUG: Output filename: {output_filename}")
        
        # Create PDF writer
        writer = PdfWriter()
        total_pages = 0
        
        # Merge PDFs with error handling
        for file_info in files:
            print(f"DEBUG: Processing file: {file_info['name']}")
            try:
                reader = PdfReader(file_info['path'], strict=False)
                
                # Validate PDF has pages
                if len(reader.pages) == 0:
                    print(f"DEBUG: Skipping empty PDF: {file_info['name']}")
                    continue
                
                # Add all pages
                for page in reader.pages:
                    writer.add_page(page)
                    total_pages += 1
                    
            except Exception as e:
                print(f"DEBUG: Error processing {file_info['name']}: {str(e)}")
                flash(f'Error processing {file_info["name"]}: {str(e)}', 'warning')
                continue
        
        # Check if any pages were added
        if total_pages == 0:
            flash('No valid pages found to merge', 'error')
            return redirect(url_for('merge'))
        
        # Save merged PDF
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        print(f"DEBUG: Saving to: {output_path}")
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"DEBUG: Merge complete. Total pages: {total_pages}")
        
        # Store in session for download
        session['merged_file'] = {
            'filename': output_filename,
            'path': output_path,
            'pages': total_pages,
            'size': f"{os.path.getsize(output_path) / 1024:.1f} KB"
        }
        
        # Add to merge history
        merge_history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': output_filename,
            'files_count': len(files),
            'total_pages': total_pages
        })
        
        flash('PDFs merged successfully!', 'success')
        return redirect(url_for('download', filename=output_filename))
        
    except Exception as e:
        print(f"DEBUG: Merge failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Merge failed: {str(e)}', 'error')
        return redirect(url_for('merge'))

@app.route('/debug')
def debug_session():
    """Debug session information"""
    debug_info = {
        'session_keys': list(session.keys()),
        'upload_id': session.get('upload_id'),
        'uploaded_files_count': len(session.get('uploaded_files', [])),
        'merged_file': session.get('merged_file'),
        'uploads_dir_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
        'output_dir_exists': os.path.exists(app.config['OUTPUT_FOLDER'])
    }
    
    # Check for existing session folders
    session_folders = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for item in os.listdir(app.config['UPLOAD_FOLDER']):
            item_path = os.path.join(app.config['UPLOAD_FOLDER'], item)
            if os.path.isdir(item_path):
                files_in_folder = [f for f in os.listdir(item_path) if f.endswith('.pdf')]
                session_folders.append({
                    'id': item,
                    'files': files_in_folder,
                    'file_count': len(files_in_folder)
                })
    
    debug_info['session_folders'] = session_folders
    
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route('/recover/<session_id>')
def recover_session(session_id):
    """Recover a session by ID"""
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    if not os.path.exists(session_folder):
        flash('Session not found', 'error')
        return redirect(url_for('index'))
    
    # Rebuild session
    uploaded_files = []
    for filename in os.listdir(session_folder):
        if filename.endswith('.pdf'):
            filepath = os.path.join(session_folder, filename)
            pdf_info = get_pdf_info(filepath)
            uploaded_files.append({
                'name': filename,
                'path': filepath,
                'pages': pdf_info['pages'],
                'size': f"{pdf_info['size'] / 1024:.1f} KB"
            })
    
    if uploaded_files:
        session['upload_id'] = session_id
        session['uploaded_files'] = uploaded_files
        flash(f'Recovered session with {len(uploaded_files)} files', 'success')
        return redirect(url_for('merge'))
    else:
        flash('No valid files found in session', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    """Download merged PDF"""
    print(f"DEBUG: Download page requested for: {filename}")
    print(f"DEBUG: Session has merged_file: {'merged_file' in session}")
    
    if 'merged_file' in session:
        print(f"DEBUG: Session merged_file: {session['merged_file']}")
        if session['merged_file']['filename'] == filename:
            file_info = session['merged_file']
            print(f"DEBUG: Rendering download page with file info: {file_info}")
            return render_template('simple_download.html', 
                                 filename=filename,
                                 pages=file_info['pages'],
                                 size=file_info['size'])
    
    print(f"DEBUG: Rendering download page without file info")
    return render_template('simple_download.html', filename=filename, pages='Unknown', size='Unknown')

@app.route('/download_file/<filename>')
def download_file(filename):
    """Actual file download"""
    file_path = os.path.abspath(os.path.join(app.config['OUTPUT_FOLDER'], filename))
    print(f"DEBUG: Download requested: {filename}")
    print(f"DEBUG: File path: {file_path}")
    print(f"DEBUG: File exists: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        try:
            return send_file(file_path, as_attachment=True, download_name=filename)
        except Exception as e:
            print(f"DEBUG: Send file error: {e}")
            return f"Download error: {e}", 500
    else:
        return f"File not found: {filename}", 404



@app.route('/history')
def history():
    """Show merge history"""
    return render_template('history.html', history=merge_history[::-1])  # Reverse for newest first

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for file upload"""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'status': 'error', 'message': 'No files provided'})
        
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(session_folder, filename)
                file.save(filepath)
                
                pdf_info = get_pdf_info(filepath)
                if pdf_info['pages'] > 0:
                    uploaded_files.append({
                        'name': filename,
                        'pages': pdf_info['pages'],
                        'size': pdf_info['size']
                    })
                else:
                    os.remove(filepath)  # Remove corrupted file
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/merge', methods=['POST'])
def api_merge():
    """API endpoint for PDF merge"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        output_filename = data.get('output_filename', 'merged.pdf')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'No session ID provided'})
        
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        if not os.path.exists(session_folder):
            return jsonify({'status': 'error', 'message': 'Session not found'})
        
        # Get all PDF files in session folder
        pdf_files = [f for f in os.listdir(session_folder) if f.endswith('.pdf')]
        pdf_files.sort()
        
        # Merge PDFs with error handling
        writer = PdfWriter()
        for filename in pdf_files:
            filepath = os.path.join(session_folder, filename)
            try:
                reader = PdfReader(filepath, strict=False)
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                print(f"DEBUG: API merge error for {filename}: {str(e)}")
                continue
        
        # Save merged PDF
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return jsonify({
            'status': 'success',
            'download_url': f'/download_file/{output_filename}',
            'filename': output_filename
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/status/<task_id>')
def api_status(task_id):
    """API endpoint to check merge status"""
    # Simple status check - in production, use proper task queue
    return jsonify({'status': 'completed', 'progress': 100})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear merge history"""
    global merge_history
    merge_history = []
    flash('History cleared successfully!', 'success')
    return redirect(url_for('history'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

@app.errorhandler(413)
def too_large(error):
    return render_template('error.html', error='File too large. Maximum size is 50MB.'), 413

@app.route('/recovery')
def recovery_page():
    """Show recovery page"""
    return render_template('recovery.html')



@app.route('/clear_session')
def clear_session():
    """Clear current session"""
    session.clear()
    flash('Session cleared', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    