import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
import parser
# from PyPDF2 import PdfFileReader, PdfFileWriter

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
try:
    os.mkdir(UPLOAD_FOLDER)
except Exception:
    print('exception')
try:
    os.mkdir(DOWNLOAD_FOLDER)
except Exception:
    print('exception')
ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__, static_url_path="/static")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# limit upload size upto 8mb
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file attached in request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            process_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), filename)
            # return redirect(url_for('display', filename=filename))
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template('index.html')

@app.route('/<filename>/')
def display(filename):
    filename = filename
    lines = get_lines(filename)
    text = get_text(filename)
    print(filename)
    runtime, syntax = parser.get_total_runtime(lines)
    # tables=[syntax.to_html(classes='data')], titles=syntax.columns.values
    return render_template('exercise.html', filename = filename, text=text, lines=lines, length = len(lines), runtime= runtime, )


def get_lines(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    file = open(path, 'r+')
    lines = file.readlines()
    file.close()
    return lines

def get_text(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    file = open(path, 'r+')
    text = file.read()
    file.close()
    return text



def process_file(path, filename):
    lines = write_dummy_file(path,filename)
    # with open(path, 'a') as f:
    #    f.write("\nAdded processed content")
    return lines

def write_dummy_file(path,filename):
    input_file = open(path,'r+')
    input_lines = input_file.readlines()
    output_stream = open(app.config['DOWNLOAD_FOLDER'] + filename, 'w+')
    output_stream.write("Test\n")
    output_stream.write(f'Total number of lines: {len(input_lines)}')
    output_stream.close()
    return input_lines
        

# def remove_watermark(path, filename):
#     input_file = PdfFileReader(open(path, 'rb'))
#     output = PdfFileWriter()
#     for page_number in range(input_file.getNumPages()):
#         page = input_file.getPage(page_number)
#         page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(), 200)
#         output.addPage(page)
#     output_stream = open(app.config['DOWNLOAD_FOLDER'] + filename, 'wb')
#     output.write(output_stream)


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for('display', filename=filename))
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
