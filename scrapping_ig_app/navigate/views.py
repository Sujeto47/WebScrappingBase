import site
from smtplib import SMTPSenderRefused
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import *
from .logic.navigate import open_application as oa
import threading
import json
import re
import requests
from bs4 import BeautifulSoup as bs
base_url = "https://www.instagram.com/"
def index(request):
    return render(request, 'navigate/index.html',{})

def users(request):
    return render(request, 'navigate/user.html',{})

def wsimgindex(request):
    #return HttpResponse("Analizando Imagenes")
    return render(request, 'navigate/webSImg.html',{})

def imgs(request):
    #return HttpResponse("Analizando Imagenes")
    return render(request, 'navigate/img.html',{})


def open_application(request):
    #user=get_object_or_404(ScraperUser, username=request.POST['login_name'])
    try:
        #Codigo Real        
        su=ScraperUser(username=request.POST['login_name'],password=request.POST['login_password'])
        u=User(username=request.POST['login_name'],profile_url=base_url+request.POST['login_name'])
        action_type = request.POST['action_type']
        su.save_user()
        u.save_user()
        oa.main(su.username, action_type)    
        #Fragmento Kevin
        """headers= {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}
        response=requests.get(urlimage, headers=headers)
        print(response.status_code)
        soup=bs(response.text,'html.parser')
        for link in soup.find_all('img'):
            rutaimagen=link.get('src')
            filename=re.search(r'/([\w_-]+[.](jpg|gif|png))',rutaimagen)
            if not filename:
                print('No hay imagen')
            else:
                try:
                    with open ("imagenes/"+filename.group(1), 'wb') as a:
                        if 'http' not in rutaimagen:
                            rutaimagen='{}{}'.format(urlimage,rutaimagen)
                        response=requests.get(rutaimagen)
                        a.write(response.content)

                except Exception as e:
                    pass   
        print ('Proceso Finalizado')"""
    except (Exception) as err:
        print(f"Unexpected {err=}, {type(err)=}")       

    return HttpResponse("Usuarios Insertados")

urlimage ='https://www.instagram.com/p/Cg51R_Mum3T/' #Variable Kevin
descargar=(urlimage)

def publications(request):
    return render(request, 'navigate/publication.html',{})

def comments(request):
    return render(request, 'navigate/comments.html',{})

def descargaimg(request):
    try:
        oa.main3()
    except (Exception) as e:
        print(f"Error {e=}, {type(e)=}")
    return render(request, 'navigate/webSImg.html',{})

def imganalizer(request):
    try:
        oa.main2()
    except (Exception) as e:
        print(f"Error {e=}, {type(e)=}")
    return render(request, 'navigate/img.html',{})