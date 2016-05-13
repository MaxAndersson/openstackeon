import os,shutil,logging,sys,getpass,uuid,time,pickle,tarfile,io,base64
from time import sleep, time
from novaclient import client


# This Utility makes an in-memory tarfile
def tarboll(source_dir):
    IO = io.BytesIO('wr')
    IOzip = io.BytesIO('wr')
    with tarfile.TarFile(fileobj=IO,mode='w') as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    IO.seek(0)
    return IO
# This Utility function collects a directory in to an in-memory tarfile and base64 encode it
def tar64(source_dir):
        return base64.b64encode(tarboll(source_dir).read())


# Translates Rc-file variables to nova api compatible
def novaconfig (cloud):
    return {
            "username" : cloud["OS_USERNAME"],
            "api_key" : cloud['OS_PASSWORD'],
            "project_id" : cloud['OS_TENANT_NAME'],
            "auth_url" : cloud['OS_AUTH_URL'],
            "region_name" : cloud['OS_REGION_NAME'],
            'connection_pool' : True

    }

# Get available resources information about the client.
def clientInfo(client):
    return{
    "images": client.images.list(),
    "flavors": client.flavors.list(),
    "key_pairs": client.keypairs.list(),
    "floating_ips": [ip for ip in client.floating_ips.list() if ip.instance_id == None],
    "floating_ip_pool": client.floating_ip_pool.list(),
    "security_groups": client.security_groups.list()
    }

#Parseing of RC-Files
def parseRC(cloud_rc):
    result = []
    for cloud in cloud_rc:
        rows = os.popen("cat " + cloud + " |grep export").read()
        rows = rows.strip().split("\n")
        rows = [row[7:] for row in rows]
        credentials = [row.split("=") for row in rows]
        print credentials
        credentials = dict([[key,value.strip('"')] for [key,value] in credentials ])
        credentials["OS_PASSWORD"] = "" #getpass.getpass("Please enter password for " + credentials["OS_USERNAME"] + "@" + credentials["OS_TENANT_NAME"] + ":" + credentials['OS_REGION_NAME'] + "\n ->")
        result.append(credentials)
    return result

# Set the password
def get_pass(credentials):
    credentials["OS_PASSWORD"] = getpass.getpass("Username: " + credentials["OS_USERNAME"] + ",\n Tenant: " + credentials["OS_TENANT_NAME"] + ",\n Region:" + credentials['OS_REGION_NAME'] +"\n Password ->" )

def auth(cred):
    if cred["OS_PASSWORD"] == "":
        get_pass(cred)
    config = novaconfig(cred)
    try:
        a_client = client.Client(version="2.0",**config)
        a_client.authenticate()
        #print a_client
    except Exception as e:
        cred["OS_PASSWORD"] = ""
        print e
        raise e
    return [config["project_id"] +":"+ config['region_name'],a_client]

def auth_rec(clouds):
        cloudsRET = []
        for cloud in clouds:
            finished = 0
            while finished is not 1:
                try:
                    cloudsRET.append(auth(cloud))
                    finished = 1
                    print "OK"
                    pass
                except Exception as e:
                    print e
                    pass
        return cloudsRET


def get_default_profile(master,project_id):
    #TODO Implement default profile handler
    if master:
        return
    else :
         return

def get_profile(cloud,master,project_id):
    #TODO Implement better structure for prj & region_name, HOTFIX!
    project_id = project_id.split(":")[0] ## HOTFIX !

    q = lambda x,y: y[0] if x == True else y[1]
    needed = ['name','key_name','flavor','image','security_group','floating_ip_pool']
    api_names = ['','keypairs','flavors','images','security_groups','floating_ip_pools']
    product = []
    profile = get_default_profile(master, project_id)

    for api,key in zip(api_names,needed):
            if api != '':
                try:
                    if api == 'floating_ip_pools':
                        # floating_ip_pools api does not support .get method()
                        ip_pool = [pool for pool in getattr(cloud,api).list() if pool.name == profile[key]].pop()
                        product.append([key,ip_pool])
                    else:
                        # Get referenced resources by id. If all are present user input is not needed
                        product.append([key,getattr(cloud,api).get(profile[key])])
                except:
                    selection = dict(enumerate([component for component in getattr(cloud,api).list()]))
                    if api == 'images':
                        a = getattr(cloud,api).list()
                        print [b.metadata for b in a]
                    for num,val in enumerate(selection.values()):
                        print str(num) + " : " + val.name
                    selected = input(q(master,["Master","Slave"]) + ": " + key + " \n [0-"+str(len(selection.values()) - 1)+"] ->")
                    product.append([key,selection[selected]])
                    pass
            else:
                if(master):
                    product.append(["name","EONMaster"])
                else:
                    product.append(["name","EONSlave"])
    #print [(key,type(a[1])) for a in product if a[0] != 'floating_ip_pool' ]
    b = [[a[0],a[1].id] for a in product if a[0] != 'name' and a[0] != 'floating_ip_pool']
    e = dict(b)
    e['name'] = dict(product)['name']
    e['floating_ip_pool'] = dict(product)['floating_ip_pool'].name
    print e
    return dict(product)

def boot_n(client, profile, number_servers):

    return [boot(client,profile,uuid.uuid1()) for n in range(0,number_servers)]

def boot(client,profile, a_id = None):
        select = lambda x,y:  dict([[k,y[k]] for k in x if k in y.keys()])
        f = open(profile['context'])
        if 'inject' in profile.keys():
            inject = ''
            for k,v in profile['inject'].items():
                inject = inject + v +'\n'
            userdata = f.readline() + inject + f.read()
        else:
            userdata = f.read()

        f.close()
        if type(profile['key_name']) is not unicode:
            profile['key_name'] = profile['key_name'].name


        profile['userdata'] = userdata
        config = select(['image','userdata','key_name','flavor','name'],profile)
        if a_id != None:
            config['name'] = profile['name'] + '-' + str(a_id)
        try:
            return client.servers.create(**config)
        except Exception as e:
            raise Exception('Booting Problem: {}'.format(e))



def _check_floating_ip_assignment(client,server):
        try:
            floating_ip = [ip for ip in client.floating_ips.list() if ip.instance_id == server.id ].pop().ip
            return floating_ip
        except:
            return None
def _check_floating_ips_reuse(client):
        return [ip for ip in client.floating_ips.list() if ip.instance_id == None]

def _get_floating_ip(client,pool):
            ip  = _check_floating_ips_reuse(client)
            if ip != []:
                return ip.pop()
            else:
                ip = client.floating_ips.create(pool)
                return ip

def _attach_floating_ip(client,server,pool):

            if(_check_floating_ip_assignment(client,server) != None):
                raise Exception('Server already has an floating IP')
            ip = _get_floating_ip(client,pool)
            try:
                print server
                server.add_floating_ip(ip)
                return ip.ip

            except Exception as e:
                raise Exception("Failed to attach a floating IP to the controller.\n{0}".format(e))
            return ip.ip

def _attach_security_group(server):
        ##TODO Seperate security groups for master and slave
        ports = [5672,15672,5000]
        security_group = [sg  for sg in client.security_groups.list() if sg.name == 'EON']
        if security_group == []:
            security_group = client.security_groups.create('EON','This security group is used by the EON OpenStack Provitioner')
            for port in ports:
                client.security_group_rules.create(security_group.id,ip_protocol='TCP',from_port = port,to_port=port)
        else:
            security_group = security_group.pop()
        server.add_security_group(security_group.id)

def strip_profile(profile):
    profile['image'] = profile['image'].id
    profile['floating_ip_pool'] = profile['floating_ip_pool'].name
    profile['flavor'] = profile['flavor'].id

def isRunning(scratchpath):

    running = os.path.join(scratchpath,'.running')
    if os.path.isfile(running):
        res = pickle.load(open(running))
        ## Check if instance is running and get ip
        return res
    else:
        return None
def save_running(results,scratchpath):
    running = os.path.join(scratchpath,'.running')
    res = pickle.dump(results,open(running,'w'))

def run(rc_files,n_workers,scratchpath,master_index = None):
        ##TODO Add in support for preconfiguration (setup.py)
        res = isRunning(scratchpath)
        if res == None:
            cloudsCred = parseRC(rc_files)
            clouds = auth_rec(cloudsCred)
            clouds = dict(clouds)
            assert(len(n_workers) == len(clouds.values()))
            selection = dict(enumerate(clouds.keys()))

            try:
                if master_index == None:
                    selected = input("Please select cloud to boot master " + str(selection) + "\n -> ")
                else:
                    selected = master_index
                master_client = clouds[selection[selected]]
                master_profile = get_profile(master_client,True,selection[selected])
                worker_prep = [{
                            "client" : client,
                            "profile" : get_profile(client,False,name),
                            "number_servers": num
                            } for client,name,num in zip(clouds.values(),clouds.keys(),n_workers)]

                master_profile['context'] = os.path.join(os.path.dirname(os.path.abspath(__file__)),'master.sh')
                master = boot(master_client,master_profile) # for now

                flag = 0
                backoff = 2
                while flag != 1:
                    try:
                        #print master.get_console_output()
                        _attach_floating_ip(master_client,master,master_profile['floating_ip_pool'].name)
                        master.add_security_group(master_profile['security_group'].name)
                        master_ip = master_client.servers.ips(master)
                        flag = 1
                    except Exception as e:
                        backoff = (backoff + 2) % 30
                        print "Backoff {} seconds: {}".format(backoff,e)
                        sleep(backoff)
                        pass

                for obj in worker_prep:
                    obj['profile']['inject'] = {"master_ip" : "MASTER_IP={}".format(master_ip)}
                    obj['profile']['context'] = os.path.join(os.path.dirname(os.path.abspath(__file__)),'slave.sh')

                workers = {str(i) : boot_n(**worker_conf) for i,worker_conf in zip(range(0,len(worker_prep)), worker_prep)}
                master_ip = master_ip[master_ip.keys()[0]][1]['addr'] ## FIXME This is not fool proof, by any means.

                workers_by_cloud = workers.values()
                worker_ids = [[worker.id for worker in worker_cloud] for worker_cloud in workers_by_cloud ]
                worker_dict = dict(zip(clouds.keys(),worker_ids))


                result = {
                    "master_index": selected,
                    "clouds": clouds.keys(),
                    "master" : master.id,
                    "master_ip" : master_ip,
                    "workers" : worker_dict,
                    "timestamp" : time()
                    }
                print save_running(result,scratchpath)
                return result
            except Exception as e:
                print "Critical exception caught, {} running".format(master_ip)
                raise e
        else:
            return res

if __name__ == "__main__":
    run()
