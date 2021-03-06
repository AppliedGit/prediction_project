from django.shortcuts import render,HttpResponse,redirect
from django.views.decorators.cache import cache_control
from django.conf import settings
import json
import requests
import pickle
import numpy as np
import sklearn
import jwt 
import datetime
import uuid
import hashlib
import pandas as pd
from functools import wraps
import os

# Create your views here.

directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
source_path = os.path.join(directory,'car_prediction')
model = pickle.load(open(source_path+'/random_forest_regression_model.pkl', 'rb')) 

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):        
        secret_key = settings.TOKEN_KEY        
        auth_time = str(args[0])
        auth_time = auth_time.replace("'","")
        auth_time = auth_time.replace(">","")
        auth_time = auth_time.split("=")
        auth_time = auth_time[1]
        auth_time = auth_time.split("&")
        auth_time = auth_time[0]
        token = ""
        if auth_time in settings.TOKEN_DIC:
            token = settings.TOKEN_DIC[auth_time]                              
        if not token:            
            settings.TOKEN_STATUS = "Token is missing"            
            return HttpResponse(json.dumps({'token_status' : settings.TOKEN_STATUS}))
        try:             
            data = jwt.decode(token, secret_key,algorithms=['HS256'])
        except Exception as e:                        
            if(str(e) == "Signature has expired" or str(e) == "Signature verification failed" ):
                settings.TOKEN_STATUS = "Token has expired" 
            else:
                settings.TOKEN_STATUS = "Error : "+str(e)            
            return HttpResponse(json.dumps({'token_status' : settings.TOKEN_STATUS}))
        settings.TOKEN_STATUS = ""
        return f(*args, **kwargs)

    return decorated

@token_required
def get_prediction_value(request):         
    Present_Price=float(request.GET["showroom_price"])
    Kms_Driven=int(request.GET["driven_kms"])
    Owner=int(request.GET["owner_type"])
    Year = int(request.GET["year"])        
    Fuel_Type_Petrol=int(request.GET["fuel_type"])             
    Year=2020-Year
    if(Fuel_Type_Petrol== 1):
        Fuel_Type_Petrol=1
        Fuel_Type_Diesel=0
        Fuel_Type_CNG=0
    elif(Fuel_Type_Petrol==2):
        Fuel_Type_Petrol=0
        Fuel_Type_Diesel=1
        Fuel_Type_CNG=0
    else:
        Fuel_Type_Petrol=0
        Fuel_Type_Diesel=0
        Fuel_Type_CNG=1
    Seller_Type_Individual=int(request.GET["seller_type"])
    if(Seller_Type_Individual==1):
        Seller_Type_Individual=1
        Seller_Type_Dealer=0
    else:
        Seller_Type_Individual=0
        Seller_Type_Dealer=1	
    Transmission_Mannual=int(request.GET["transmission_type"])   
    if(Transmission_Mannual==1):
        Transmission_Mannual=1
        Transmission_Automatic=0
    else:
        Transmission_Mannual=0
        Transmission_Automatic=1 
    prediction = model.predict([[Present_Price,Kms_Driven,Owner,Year,Fuel_Type_CNG,Fuel_Type_Diesel,Fuel_Type_Petrol,Seller_Type_Dealer,Seller_Type_Individual,Transmission_Automatic,Transmission_Mannual]])
    return HttpResponse(json.dumps({'token_status': '','prediction_val' : prediction[0]}))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):        
    return render(request,'prediction.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):                        
    return render(request,'login.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def token_error(request):
    return render(request,'login.html',context={'login_status': settings.TOKEN_STATUS}) 

def token_status(request):
    return HttpResponse(settings.TOKEN_STATUS)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):        
    auth_login_time = request.GET["b9297e16791de8e8bff0fb7870682121f94fd89acfd8506be4662e238495141916eed2100b21724a35927e0e7867007c470564c80bf7d9a971d490b817a05e31"]    
    if auth_login_time in settings.TOKEN_DIC:
        settings.TOKEN_DIC.pop(auth_login_time)      
    logout_success = "78661b2fac117e9c9764a46403d20579e49974a5aa004922573cf08150c16de8365196319d6662187bde83ae9d6669956a13e2ea22ddb801e15df3887b2252ec"    
    return HttpResponse(logout_success)    

@token_required
def get_prediction_table_data(request):                           
    year,present_price,kms_driven,owner,fuel_type,seller_type,transmission_type,car_name,selling_price = [],[],[],[],[],[],[],[],[]
    car_year = []
    test_df = pd.read_csv(source_path+'/car_data_test.csv')        
    json_string = test_df.to_json(orient='index',index=True)
    json_dictionary = json.loads(json_string)
        
    for key in json_dictionary:   
        car_config = json_dictionary[key]                
        Present_Price=car_config["Present_Price"]
        Kms_Driven=car_config["Kms_Driven"]
        Owner=car_config["Owner"]
        Year = car_config["Year"]        
        Fuel_Type_Petrol=car_config["Fuel_Type_Petrol"]           
        Year=2020-Year
        if(Fuel_Type_Petrol=='Petrol'):
            Fuel_Type_Petrol=1
            Fuel_Type_Diesel=0
            Fuel_Type_CNG=0
        elif(Fuel_Type_Petrol=='Diesel'):
            Fuel_Type_Petrol=0
            Fuel_Type_Diesel=1
            Fuel_Type_CNG=0
        else:
            Fuel_Type_Petrol=0
            Fuel_Type_Diesel=0
            Fuel_Type_CNG=1
        Seller_Type_Individual=car_config["Seller_Type_Individual"]
        if(Seller_Type_Individual=='Individual'):
            Seller_Type_Individual=1
            Seller_Type_Dealer=0
        else:
            Seller_Type_Individual=0
            Seller_Type_Dealer=1	
        Transmission_Mannual=car_config["Transmission_Mannual"]
        if(Transmission_Mannual=='Manual'):
            Transmission_Mannual=1
            Transmission_Automatic=0
        else:
            Transmission_Mannual=0
            Transmission_Automatic=1 
        prediction = model.predict([[Present_Price,Kms_Driven,Owner,Year,Fuel_Type_CNG,Fuel_Type_Diesel,Fuel_Type_Petrol,Seller_Type_Dealer,Seller_Type_Individual,Transmission_Automatic,Transmission_Mannual]])
        selling_price.append(prediction[0])        
        present_price.append(Present_Price)
        kms_driven.append(car_config["Kms_Driven"] )
        owner.append(car_config["Owner"] )
        year.append(car_config["Year"] )
        fuel_type.append(car_config["Fuel_Type_Petrol"] )
        seller_type.append(car_config["Seller_Type_Individual"] )
        transmission_type.append(car_config["Transmission_Mannual"] )
        car_name.append(car_config["Car_Name"] )                               
    
    prediction_result = {'token_status': '',"selling_price" : selling_price,"present_price":present_price,"kms_driven":kms_driven,"owner":owner,"year" : year,"fuel_type":fuel_type,"seller_type":seller_type,"transmission_type":transmission_type,"car_name":car_name,
    "max_selling_price" : max(selling_price),"max_showroom_price":max(present_price),"unique_car":get_unique_numbers(car_name)}        
    return HttpResponse(json.dumps(prediction_result))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def get_auth_token(request):            
    uname_hash = 'c7ad44cbad762a5da0a452f9e854fdc1e0e7a52a38015f23f3eab1d80b931dd472634dfac71cd34ebc35d16ab7fb8a90c81f975113d6c7538dc69dd8de9077ec'      
    password_hash = '263d198e179108ea11ade755d21829b31eb6744f888c77b4bf704472eb70020eed618bbf2b43883484356a2a315b98f622bcdefdafc465e7aaba1a12cef2b0f6'       
    auth_pwd = request.GET["password"].encode('utf-8')
    auth_password_hash = hashlib.sha512(auth_pwd).hexdigest() 
    auth_uname = request.GET["username"].encode('utf-8')
    auth_uname_hash = hashlib.sha512(auth_uname).hexdigest() 
    result = ""   
    settings.TOKEN_STATUS = "Token is invalid"
    auth_login_time = str(datetime.datetime.utcnow())
    auth_login_time = hashlib.sha512(auth_login_time.encode('utf-8')).hexdigest()     
    if auth_uname_hash == uname_hash and auth_password_hash == password_hash: 
        secret_key = str(uuid.uuid4().hex)        
        unique_id = str(uuid.uuid4().hex)
        token = jwt.encode({'user' : unique_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, secret_key)                             
        try:             
            data = jwt.decode(token, secret_key,algorithms=['HS256'])    
            result = token
            settings.TOKEN_NAME = result
            settings.TOKEN_KEY = secret_key
            settings.TOKEN_DIC[auth_login_time] = result
            settings.TOKEN_STATUS = "51e85deb51c2b909a21ec5b8e83b1cb28da258b1be227620105a345a2bd4c6aea549cd5429670f2df33324667b9f623a420b3a0bdbbd03ad48602211e75478a7"
        except Exception as e:                       
            settings.TOKEN_STATUS = "Error : "+str(e)                        
            #return render(request,'login.html',context={'login_status':str(e) })
    else:
        settings.TOKEN_STATUS = "Invalid Username or Password"    
    
    token_result = {
    "b9297e16791de8e8bff0fb7870682121f94fd89acfd8506be4662e238495141916eed2100b21724a35927e0e7867007c470564c80bf7d9a971d490b817a05e31":auth_login_time,
    "45270d7fc39f9b812bc348a10c53fe80920ca866eefc4b8e5eefe20590fa319a655ff8e571caf8e757dc83a024b6f3e02063e4780d635636f233c1e6e05f2591":settings.TOKEN_STATUS}
    return HttpResponse(json.dumps(token_result))

def get_unique_numbers(numbers):
    list_of_unique_numbers = []
    unique_numbers = set(numbers)
    for number in unique_numbers:
        list_of_unique_numbers.append(number)
    return list_of_unique_numbers
    
