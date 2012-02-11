from datetime import datetime, date

"""
REPLACE THE FOLLOWING WITH YOUR SETTINGS
"""
orig = "db_reload.json"  #INPUT FILE
appfolder = "/root/app_name"
approot = "/root"


#Setup the script environment
import os
import sys

settings_path = [appfolder, approot] #LOCATION OF SETTINGS.PY FILE, ROOT
sys.path = sys.path + settings_path
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
from django.core.management import setup_environ
setup_environ(settings)


import json
from django.db.models import get_model 
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import ForeignKey, OneToOneField
from django.db.transaction import commit_on_success


file = open(orig, 'r')
items = json.load(file)

@commit_on_success
def run(items):
    while len(items) > 0:
        for obj in items:
            if obj:
                save_instance = True
                model = get_model(obj['app'], obj['model'])
                data = obj['data']
                
                try:
                    #make sure the instance doesn't already exist, if it does, skip and remove from data items
                    model.objects.get(id=data['id'])
                    del items[items.index(obj)]
                    continue
                except (ObjectDoesNotExist, KeyError):
                    #clean the data fields from JSON serialized
                    for f in model._meta.fields:
                        value = data[f.name]
                        if value is None:
                            del obj['data'][f.name]
                            continue
                        elif isinstance(f, date):
                            try:
                                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                            except ValueError:
                                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
                            obj['data'][f.name] = value
                        elif isinstance(f, ForeignKey):
                            try:
                                rel_model = f.rel.to.objects.get(id=value)
                                obj['data'][f.name] = rel_model
                            except ObjectDoesNotExist:
                                #if the related object is not already in the db, skip until it is
                                save_instance = False
                if save_instance: 
                    #save the instance based on the cleaned data ane remove from data items
                    instance = model(**obj['data'])
                    instance.save()
                    print model.__name__, 'saved'
                    del items[items.index(obj)]
                

run(items)
                
                
                


















