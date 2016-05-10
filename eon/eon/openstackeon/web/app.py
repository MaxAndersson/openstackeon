#!flask/bin/python
import os, subprocess,io,shlex
from flask import Flask, jsonify, render_template,request,redirect,url_for
from werkzeug import secure_filename
import zipfile
UPLOAD_FOLDER = './eonworks'
STATIC_FOLDER = './static'
TEMPLATES_FOLDER = './templates'
ALLOWED_EXTENSIONS = set(['tar','zip'])

EON_PATH = 'python ../../basinhopping.py'
map(check_folders, [UPLOAD_FOLDER,STATIC_FOLDER,TEMPLATES_FOLDER])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def check_folders(path):
    if not os.path.isdir(path):
        os.mkdir(path)
    else:
        print 'Needs path: 'path

def allowed_file(filename):
    print filename.rsplit('.', 1)[1]
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def unpack(a_file,path):
    f = a_file.filename.rsplit('.',1)[1]
    if f == 'zip':
        fi = zipfile.ZipFile(a_file)
        fi.extractall(app.config['UPLOAD_FOLDER'])
        print 'zip zip'

    elif f == 'tar':
        print "tar files not yet supported"


def dirs_with_config():
    topdir = app.config['UPLOAD_FOLDER']
    exten = '.ini'
    count = 0
    paths=[]
    for dirpath, dirnames, files in os.walk(topdir):
        for name in files:
            if name.lower().endswith(exten):
                paths.append(dirpath)
    return paths

@app.route('/exec')
def execute_job():
    paths = dirs_with_config()
    relative = [path.split('/')[-1] for path in paths]
    links = ['<a href={}>{}</a>'.format(url_for('execute_work',path = rel),rel) for rel in relative]
    return '''{}'''.format('<br>'.join(links))

@app.route('/exec/<path>')
def execute_work(path):
    a_dir = os.path.join(app.config['UPLOAD_FOLDER'],path)
    IO = io.FileIO('buffer','w+')
    home = os.path.realpath('.')
    os.chdir(os.path.dirname(a_dir))
    command = '{}'.format(EON_PATH)
    subprocess.Popen(shlex.split(command), stdout= IO, stderr = IO).wait()
    os.chdir(home)
    IO.seek(0)
    output = IO.read()
    try:
        logs = ' '.join([s.replace('\n','<br>') for s in filter(lambda x: 'INFO:communicator' in x,open(os.path.join(os.path.dirname(a_dir),'bh.log')).readlines())]) ## GETS comm logs
    except Exception as e:
        logs = ""
        pass

    return '''
        <!doctype html>
        <html>
        <title>Upload new File</title>
        <body>
        <h1>Output</h1>
        <div>{}</div>

        <a href="{}">rerun</a> <a href={}>results</a>
        <div background-color="grey">{}</div>
        </body>
        </html> '''.format(output,url_for('execute_work',path = path),url_for('results'),logs)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = file.filename
            print filename
            unpack(file,os.path.join(app.config['UPLOAD_FOLDER'],filename.rsplit('.',1)[0]))
            dirs_with_config()
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('upload_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <html>
    <title>Upload new File</title>
    <body>
    <h1>Upload new File</h1>
    <form action="/" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
        <input type=submit value=Upload>
    </form>
    </body>
    </html>
    '''

def con_2_png():
# The top argument for walk
    topdir = app.config['UPLOAD_FOLDER']
    outdir = './static'
    images = []
# The extension to search for
    exten = '.con'
    count = 0
    for dirpath, dirnames, files in os.walk(topdir):
        for name in files:
            if name.lower().endswith(exten):
                print(os.path.join(dirpath, name))
                inp = os.path.join(dirpath, name)
                out = os.path.join(outdir, name + str(count) + '.png')
                count = count + 1
                subprocess.call(['ase-gui',inp, '-o',out])
                images.append(out)
    return images

#TODO Add Selective results
@app.route('/results', methods = ['GET'])
def results():
    return render_template('index.html', images = con_2_png())
if __name__ == '__main__':

    app.run(#host='0.0.0.0',
                debug=True)
