from celery import Celery
import subprocess
import base64,os,io,tarfile


app = Celery('tasks',
             broker='amqp://130.238.29.37',
             backend ='amqp://130.238.29.37'
             )

CLIENT_PATH = '/eonclient'

def tarboll(source_dir):
    IO = io.BytesIO('wr')
    IOzip = io.BytesIO('wr')
    with tarfile.TarFile(fileobj=IO,mode='w') as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    IO.seek(0)
    return IO
def update(new_broker):
    app = Celery('tasks',broker='amqp://{}'.format(new_broker),backend='amqp')

def tar64(source_dir):
        return base64.b64encode(tarboll(source_dir).read())
@app.task()
def hello(message = 'random'):
    print "hello {}".format(message)

@app.task(bind=True, name ='tasks.eon_work')
def eon_work(self,message,path):
    request_id = self.request.id
    print base64.b64decode(message)
    IO = io.BytesIO(base64.b64decode(message))
    job_path = '/tmp/eon_jobs/' + request_id
    print job_path
    with tarfile.TarFile(fileobj=IO,mode='r') as tar:
        tar.extractall(job_path)
        tar.close()
    command = "cd {}; {}".format(os.path.join(job_path,path),CLIENT_PATH)
    datFile = open(os.path.join(job_path,'stdout.out'),'w')
    p = subprocess.Popen(command, stdout=datFile, stderr=subprocess.PIPE, shell=True)
    p.wait()

    datFile.close()
    datFile = open(os.path.join(job_path,'stdout.out'),'r')
    a = datFile.read()
    return (path, base64.b64encode(a))

if __name__ == '__main__':
    app.start()
