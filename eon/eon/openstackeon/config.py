#!/usr/bin/env python
import os,sys,novaclient,base64,pickle
from helpers import *

def make_profile(client):
    profile = {}
    exit = 0
    def print_selection(selection):
        for i, select in enumerate(selection):
            print '[',i,'] ', select
    while exit == 0:
        print 'Current profile: '
        for key, value in profile.items():
            print key,' : ',value
        selection = ['Select Image','Select Flavor','Select Key Pair', 'Select Floating Ip Pool', 'Select Security Group','Package & Quit']
        print_selection(selection)
        selected = input('Select Action [0-{}] ->'.format(len(selection) -1))
        if selected == 0:
            images = [image for image in client.images.list() if 'eon' in image.name or 'Ubuntu' in image.name ]
            print_selection(images)
            profile['image'] = images[int(input('Select Image: '))].id
        elif selected == 1:
            flavors = client.flavors.list()
            print_selection(flavors)
            profile['flavor'] = flavors[int(input('Select Flavor: '))].id
        elif selected == 2:
            keys = client.keypairs.list()
            print_selection(keys)
            profile['key_name'] = keys[int(input('Select key pair'))].name
        elif selected == 3:
            pools = client.floating_ip_pools.list()
            print_selection(pools)
            profile['floating_ip_pool'] = pools[int(input('Select floating ip pool: '))].name
        elif selected == 4:
            secgroups = client.security_groups.list()
            sel = [group.name for group in secgroups]
            print_selection(sel)
            profile['security_group'] = secgroups[int(input('Select Security group'))].id
        elif selected == 5:
            ## Add validation
            obj = pickle.dumps(profile)
            obj64 = base64.b64encode(obj)
         #   print "Configureation String = {}".format(obj64)
            return obj64


def config(clouds, profiles_config = None):
    regions = clouds.keys()
    clients = clouds.values()
    print regions, clients
    def print_selection(selection):
        for i, select in enumerate(selection):
            print '[',i,'] ', select
    store = []
    if profiles_config == None:
        profiles = {}
    else:
        f = open(profiles_config)
        profiles = pickle.loads(base64.b64decode(f))

    exit = 0
    selection = ['Add master profile to a region','Add slave profile to a region','Build contextulizeation', 'Package & Exit']
    print "Please make sure all regions that will have a master or slave have a profile, respectivly"
    while exit == 0:
        print 'Current Profiles: '
        for (region,a_type, config) in store:
            print region,a_type,' : ',config

        print_selection(selection)
        selected = input('Select Action [0-{}] ->'.format(len(selection)-1))
        if selected == 0:
            print_selection(regions)
            region = int(input('Select region to add master :'))
            client = clients[region]
            a_region = regions[region]
            config = make_profile(client)
            store.append((a_region,'master',pickle.loads(base64.b64decode(config))))

        elif selected == 1:
            print_selection(regions)
            region = int(input('Select region to add slave :'))
            client = clients[region]
            a_region = regions[region]
            config = make_profile(client)
            store.append((a_region,'slave',pickle.loads(base64.b64decode(config))))
        elif selected == 2:
            print "Building, please make sure the building process is complete before you save"


        elif selected == 3:
            ##TODO Add validation
            for region in regions:
                res = {}
                for (a,b,c) in store:
                    if a == region:
                        res.update({b:c})
                profiles.update({region:res})
            if profiles_config != None:
                pickle.dump(profiles,profiles_config)
                return
            else:
                obj = pickle.dumps(profiles)
            obj64 = base64.b64encode(obj)
            print "Configureation String = {}".format(obj64)
            exit = 1
            return obj
def main():
    rc = sys.argv[1:]
    parse = parseRC(rc)
    clouds =  dict(auth_rec(parse))
    f= open ('.profiles','wr')
    config(clouds,f)
if __name__ == '__main__':
    main()
