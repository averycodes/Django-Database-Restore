from datetime import datetime, date

"""
REPLACE THE FOLLOWING WITH YOUR SETTINGS
"""
dest = "db_reload.json"  #OUTPUT FILE
backup_date = datetime(year=2012, month=2, day=2, hour=16, minute=50) #TIME OF FUCKUP or LAST DB BACKUP
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
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import ForeignKey
from decimal import Decimal



def SerializeQ(q):
    """
    Functiion to take a model instance and serialize in this format
    {
        'model': model name,
        'app': app name,
        'data': {
            model field: instance value,
        }
    
    }
    """
    if q:
        print 'q', q, q.__class__
        model = q.__class__
        data = {} #empty data dictionary
        for i in model._meta.fields:
            field = i.name
            attr = getattr(q, field)
            
            if attr:
                try:
                    #check to see if the field is serializable
                    json.dumps({field: attr})
                    data.update({field:attr})
                except TypeError:
                    #if the attribute can't be serialized check it against conditions
                    if '_ptr' in field:
                        #eliminate pointer fields (issue from PolymorphicModels)
                        continue
                    elif isinstance(i, date):
                        data.update({field:attr.isoformat()})
                    elif isinstance(i, ForeignKey):
                        data.update({field:attr.pk})
                    elif isinstance(i, Decimal):
                        data.update({field:"%.2f" % attr})
                    else:
                        #anything else that isn't serializable, convert to string
                        #TODO: Double check to make sure there aren't other field types that should be treated individually
                        data.update({i.name: "%s" % attr})
            else:
                #if the attribute is null, set it as such
                data.update({i.name:None})
        instance_data = {
            'model': model._meta.module_name,
            'app': model._meta.app_label,
            'data':data
        }    
        return instance_data
    else:
        #return an empty dictionary if instance was NoneType
        return {}

    
    
all_models = models.get_models() #All the models from every app Django knows about
json_data = [] #Empty JSON data array

models_addressed = []
for m in all_models:
    fields = m._meta.fields
    if 'created' in [i.name for i in fields]:
        qset = m.objects.filter(created__gte=backup_date)
        print m.__name__, qset.count()
        for q in qset:
            instance_data = SerializeQ(q)
            json_data.append(instance_data)
            
            #check each q for related objects referencing it
            links = [rel.get_accessor_name() for rel in q._meta.get_all_related_objects()]
            for link in links:
                try:
                    objs = getattr(q, link).all()
                except AttributeError:
                    objs = [getattr(q, link)]
                except ObjectDoesNotExist:
                    objs = []
                for o in objs:
                    instance_data = SerializeQ(o)
                    json_data.append(instance_data)

                
        #Check all the fields for foreign key references that may need to be followed
        for instance in [getattr(q, f.name) for f in q._meta.fields if type(f) == models.fields.related.ForeignKey]:
            instance_data = SerializeQ(instance)
 
                
#write everything to the json file
file = open(dest, 'w')
file.write(json.dumps(json_data))
file.close()





