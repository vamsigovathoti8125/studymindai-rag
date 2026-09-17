#!/usr/bin/env python3
"""
StudyMind AI - Lightweight Flask Version (Alternative to Streamlit)
For systems where Streamlit dependencies are difficult to install.

Run with: python app_flask.py
Then open http://localhost:5000 in your browser
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.ingest import extract_pages_from_pdf, chunk_pages
    from src.vectorstore import get_embeddings, build_faiss_index, search_index, load_index, save_index
    from src.tools.rag_tool import format_retrieved_chunks
    from src.agent.agent import decide_tool
    from src.tools.calculator import calculate
    from src.gemini_client import answer_resume_question, expand_project_documents, expand_resume_documents, extract_candidate_name, generate_text
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all src modules are in the src/ directory")
    sys.exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Session data
sessions = {}

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>StudyMind AI</title>
    <link rel="icon" type="image/jpeg" href="/favicon.jpeg">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        
        .sidebar {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .main {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
        }

        .creator-footer {
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.96);
            border-radius: 12px;
            padding: 14px 20px;
            text-align: center;
            color: #667085;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
            font-size: 13px;
        }

        .creator-footer strong {
            color: #344054;
        }

        .creator-footer a {
            color: #596fe3;
            text-decoration: none;
            margin-left: 12px;
        }

        .creator-footer a:hover {
            text-decoration: underline;
        }
        
        h1 {
            font-size: 28px;
            margin-bottom: 10px;
            color: #667eea;
        }
        
        h2 {
            font-size: 18px;
            margin: 20px 0 10px 0;
            color: #333;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }
        
        .divider {
            border: none;
            height: 1px;
            background: #eee;
            margin: 20px 0;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-weight: 500;
            margin-bottom: 5px;
            color: #333;
            font-size: 14px;
        }
        
        input[type="file"],
        select,
        input[type="number"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        
        input[type="file"] {
            padding: 5px;
        }
        
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            font-size: 14px;
            transition: background 0.3s;
            width: 100%;
        }
        
        button:hover {
            background: #5568d3;
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 400px;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            border: 1px solid #eee;
            padding: 15px;
            border-radius: 8px;
            background: #f9f9f9;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
            line-height: 1.5;
            font-size: 14px;
        }
        
        .message.user {
            background: #e3f2fd;
            text-align: right;
            margin-left: 50px;
        }
        
        .message.assistant {
            background: #f5f5f5;
            margin-right: 50px;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .status {
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 10px;
            font-size: 13px;
        }
        
        .status.info {
            background: #e3f2fd;
            color: #1976d2;
            border-left: 4px solid #1976d2;
        }
        
        .status.success {
            background: #e8f5e9;
            color: #388e3c;
            border-left: 4px solid #388e3c;
        }
        
        .status.error {
            background: #ffebee;
            color: #c62828;
            border-left: 4px solid #c62828;
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h1>🧠 StudyMind AI</h1>
            <p class="subtitle">Agentic RAG Study Assistant</p>
            
            <hr class="divider">
            
            <h2>⚙️ Settings</h2>
            <div class="form-group">
                <label>Top K Results</label>
                <input type="number" id="topK" min="1" max="10" value="4">
            </div>
            
            <hr class="divider">
            
            <h2>📚 Knowledge Base</h2>
            <div class="form-group">
                <label>Upload PDFs</label>
                <input type="file" id="fileInput" multiple accept=".pdf">
            </div>
            <button onclick="processDocuments()">Process Documents</button>
            <div id="fileStatus"></div>
        </div>
        
        <div class="main">
            <h1>🧠 StudyMind AI</h1>
            <p class="subtitle">Your Personal AI Study Assistant</p>
            
            <div id="statusMessage"></div>
            
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message assistant">
                        👋 Hello! I'm StudyMind AI. Upload your study materials and ask me questions about them.
                    </div>
                </div>
                
                <div class="input-group">
                    <input type="text" id="questionInput" placeholder="Ask something about your study materials..." 
                           onkeypress="if(event.key==='Enter') sendQuestion()">
                    <button onclick="sendQuestion()">Send</button>
                </div>
            </div>
        </div>

        <footer class="creator-footer">
            Created by <strong>Govathoti Vamsi</strong>
            <a href="mailto:vamsigovathoti8125@gmail.com">vamsigovathoti8125@gmail.com</a>
            <a href="https://www.linkedin.com/in/vamsigovathoti8125/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
            <a href="tel:+918125723070">8125723070</a>
        </footer>
    </div>
    
    <script>
        async function processDocuments() {
            const files = document.getElementById('fileInput').files;
            if (files.length === 0) return;
            
            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }
            
            updateStatus('Processing documents...', 'info');
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    updateStatus('✅ Knowledge base built successfully!', 'success');
                    document.getElementById('fileStatus').innerHTML = 
                        `<div class="status success">${result.count} documents processed</div>`;
                } else {
                    updateStatus('❌ ' + result.error, 'error');
                }
            } catch (error) {
                updateStatus('❌ Error: ' + error, 'error');
            }
        }
        
        async function sendQuestion() {
            const question = document.getElementById('questionInput').value.trim();
            if (!question) return;
            
            // Add user message to chat
            addMessage(question, 'user');
            document.getElementById('questionInput').value = '';
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: question,
                        topK: parseInt(document.getElementById('topK').value)
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    addMessage(result.answer, 'assistant');
                } else {
                    addMessage('❌ Error: ' + result.error, 'assistant');
                }
            } catch (error) {
                addMessage('❌ Error: ' + error, 'assistant');
            }
        }
        
        function addMessage(text, role) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function updateStatus(message, type) {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.jpeg')
def favicon():
    return send_from_directory(Path(__file__).parent / 'assets', 'profile.jpeg')

@app.route('/api/process', methods=['POST'])
def process_documents():
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'error': 'No files uploaded'})
        
        all_docs = []
        for file in files:
            if file.filename.endswith('.pdf'):
                pdf_bytes = file.read()
                pages = extract_pages_from_pdf(pdf_bytes, file.filename)
                chunks = chunk_pages(pages)
                all_docs.extend(chunks)
        
        if all_docs:
            texts = [d["text"] for d in all_docs]
            embeddings = get_embeddings(texts)
            index, _ = build_faiss_index(embeddings)
            save_index(index, all_docs)
            
            return jsonify({
                'success': True,
                'count': len(all_docs),
                'message': 'Knowledge base built successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'No valid PDFs found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        question = data.get('question', '')
        top_k = data.get('topK', 4)
        
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'})
        
        # Load index
        index, docs = load_index()
        if index is None:
            return jsonify({'success': False, 'error': 'Knowledge base not ready'})
        
        # Get embeddings
        q_emb = get_embeddings([question])[0]
        ids, _ = search_index(index, q_emb, k=top_k)
        retrieved = []
        seen_chunks = set()
        for i in ids:
            if i < len(docs):
                chunk_key = (docs[i].get('source'), docs[i].get('page'), docs[i].get('text', '').strip())
                if chunk_key not in seen_chunks:
                    seen_chunks.add(chunk_key)
                    retrieved.append(docs[i])
        retrieved = expand_project_documents(question, docs, retrieved)
        retrieved = expand_resume_documents(question, docs, retrieved)
        
        # Decide tool
        tool = decide_tool(question)
        
        if tool == "calculator":
            try:
                result = calculate(question)
                answer = f"Calculation Result: {result}"
            except Exception as e:
                answer = f"Calculator error: {e}"
        else:
            context = format_retrieved_chunks(retrieved)
            resume_answer = answer_resume_question(question, context)
            if resume_answer:
                answer = resume_answer
            elif 'name' in question.lower() and extract_candidate_name(context):
                answer = f"The candidate's name is {extract_candidate_name(context)}."
            else:
                prompt = (
                    "You are a helpful study assistant. Answer using only the provided context.\n\n"
                    f"Context:\n{context}\n\nQuestion: {question}"
                )
                answer = generate_text(prompt, max_output_tokens=512)
        
        # Add sources
        sources = []
        for d in retrieved:
            sources.append(f"• {d.get('source')} — p.{d.get('page')}")
        
        if sources:
            answer = answer + "\n\nSources:\n" + "\n".join(dict.fromkeys(sources))
        
        return jsonify({'success': True, 'answer': answer})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🧠 StudyMind AI - Flask Version")
    print("="*50)
    print("\nStarting server at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
