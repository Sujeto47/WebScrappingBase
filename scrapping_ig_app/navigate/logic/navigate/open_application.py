from http.client import HTTPResponse
from warnings import catch_warnings
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from ...models import User, Publication, Comment, Image, Catalog
import time
from datetime import datetime
from bs4 import BeautifulSoup
import sys

from selenium.webdriver.edge.options import Options
import pandas as pd
from shutil import rmtree
import csv

from cv2 import cv2
import easyocr
import numpy as np
import imutils
import os
import pathlib
from PIL import Image
import psycopg2

base_url = "https://www.instagram.com/"
def main(username, action_type):
    sys.setrecursionlimit(10000)
    try:
        login_url = "accounts/login/"
        option = webdriver.ChromeOptions()
        option.add_argument("--incognito")
        driver = webdriver.Chrome("../chromedriver/chromedriver", chrome_options=option)
        url=base_url+ login_url
        driver.get(url)
        time.sleep(2)
        username_input = driver.find_element(By.NAME,"username")
        username_input.send_keys("mentaldata")
        password_input = driver.find_element(By.NAME,"password")
        password_input.send_keys("smart_webscraping"+ Keys.ENTER)
        #wait=WebDriverWait(driver,120).until(EC.url_changes(url))
        login(driver,username, action_type)
    except TimeoutException as ex:
        driver.close()
def login(driver, username, action_type):
    try :        
        url=driver.current_url
        if ("https://www.instagram.com/accounts/onetap" in url):
            element=driver.find_element(By.XPATH,"//button[contains(@class, 'sqdOP yWX7d    y3zKF     ')]")
            element.click()
            time.sleep(1)
            login(driver,username, action_type)
        elif (url == "https://www.instagram.com/"):
            if (action_type == 'navigate_users'):
                navigate_followers(driver,username)
            elif (action_type == 'navigate_publications'):
                navigate_publications(driver)
            elif (action_type == 'navigate_comments'):
                navigate_comments(driver)
        else:
            login(driver,username, action_type)     

    except TimeoutException as ex:
        driver.close()

def navigate_followers(driver,original_user):
    try:
        print("Aqui estamos")
        url = driver.current_url
        driver.get(url+original_user+"/" )
        time.sleep(2)
        element=driver.find_element(By.XPATH,"//a[@href='/"+original_user+"/following/']")
        element.click()
        time.sleep(2)
        scroll_modal_users(driver)
        users = driver.find_elements(
            By.XPATH, "//span[contains(@class, '_aacl _aaco _aacw _adda _aacx _aad7 _aade')]")
        save_users(users,original_user)
        driver.close()
    except TimeoutException as ex:
        driver.close()
    except NoSuchElementException:
        print("NoSuchElementException")
        driver.close()

def save_users(users,original_user):
    following_user=User.objects.get(username=original_user)
    for u in users:
        user = User(username=u.text, profile_url=base_url+u.text)
        user.save_user()
        user_from_db = User.objects.get(username=user.username)
        following_user.user_following.add(user_from_db)
        

def scroll_modal_users(driver):
    scroll = 500
    height=0
    last_height=0
    new_height=10
    count=0
    while True :
        last_height=height
        driver.execute_script(
            "document.querySelector('._aano').scrollTop = "+str(scroll))
        height = int(driver.execute_script(
            "return document.querySelector('._aano').scrollTop"))
        new_height = height
        
        if (last_height == new_height):
            count=count+1
        else:
            count=0
        time.sleep(0.5)        
        if( height>=scroll):
            scroll = scroll*height
        
        if(count>2):
            print("end scrolling")
            break; 

def scroll_publications(driver,u):
    SCROLL_PAUSE_TIME = 1
    while True:

        # Get scroll height
        ### This is the difference. Moving this *inside* the loop
        ### means that it checks if scrollTo is still scrolling 
        last_height = driver.execute_script("return document.body.scrollHeight")
        #print(last_height)
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        posts = driver.find_elements(By.XPATH,"//div[contains(@class, '_aabd _aa8k _aanf')]")
        save_posts(posts,u)
        u.is_reviewed=True
        u.save()
        if new_height == last_height:

            # try again (can be removed)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")

            # check if the page height has remained the same
            if new_height == last_height:
                # if so, you are done
                break
            # if not, move on to the next loop
            else:
                last_height = new_height
                continue

def navigate_publications(driver):
    try :
        users = User.objects.filter(is_reviewed = False)
        for u in (users):
            url = u.profile_url
            driver.get(url)
            time.sleep(2)
            get_user_details(driver,u)
            scroll_publications(driver,u)            
            wait = WebDriverWait(driver,120).until(EC.url_changes(url))
            print(wait)
            
    except TimeoutException as ex:
        driver.close()
    finally:
        driver.close()
def save_posts(posts,instagram_user):
    for i in posts:
        tag=i.find_element(By.TAG_NAME,"a").get_attribute("href")
        p = Publication(publication_url=tag, user=instagram_user)
        p.save_publication()




def navigate_comments(driver):
    
    try :
        publications = Publication.objects.filter(is_reviewed = False)
        for p in (publications):
            url = p.publication_url
            driver.get(url)
            time.sleep(2)
            get_publication_details(driver,p)
            scroll_comments(driver,p)           
                 
    except TimeoutException as ex:
        driver.close()
    finally:
        driver.close()

def process_comments(general_comments,publication):
    i=0
    for gc in (general_comments):
        source = gc.get_attribute('innerHTML') 
        soup = BeautifulSoup(source, "html.parser")
        
        owner=soup.find("a")
        user = User(username=owner.text,profile_url=base_url+owner.text)
        user.save_user() 
        user_from_db = User.objects.get(username=user.username)
               
        text = soup.find("span",{"class":"_aacl _aaco _aacu _aacx _aad7 _aade"})
        
        comment_dt = soup.find("time")
        format_data = "%Y-%m-%dT%H:%M:%S.%fZ"
        comment_dt  = datetime.strptime(comment_dt['datetime'], format_data)

        comment = Comment(text=text.text,user=user_from_db,comment_url=user_from_db.username+"/"+str(publication.id)+str(i),publication=publication, comment_date=comment_dt)
        comment.save_comment()
        i+=1
        
def scroll_comments(driver,p):
    scroll = 400
    height=0
    last_height=0
    new_height=10
    count=0
    while True :
        try:
            general_comments = driver.find_elements(By.XPATH,"//div[contains(@class, '_a9zr')]")       
            p.is_reviewed=True
            p.save()
            time.sleep(1)
            if (len(general_comments)==0): 
                print('No se encontraron comentarios')
                break
            process_comments(general_comments,p)

            last_height=height
            driver.execute_script("document.querySelector('#react-root > div > div > section > main > div > div.ltEKP > article > div > div.qF0y9.Igw0E.IwRSH.eGOV_.acqo5._4EzTm > div > div.eo2As > div.EtaWk > ul').scrollTop = "+str(scroll))   
            height = int(driver.execute_script("return document.querySelector('#react-root > div > div > section > main > div > div.ltEKP > article > div > div.qF0y9.Igw0E.IwRSH.eGOV_.acqo5._4EzTm > div > div.eo2As > div.EtaWk > ul').scrollTop"))
            new_height = height
            
            if (last_height == new_height):
                count=count+1 
            else:
                count=0
            time.sleep(1)        
            if( height>=scroll):
                scroll = scroll*height
            
            if(count>2):
                try:
                    more_comments_button=driver.find_element(By.XPATH,"//div[contains(@class, '             qF0y9          Igw0E     IwRSH        YBx95     acqo5   _4EzTm                                                                                                            NUiEW  ')]/button")
                    more_comments_button.click()
                    time.sleep(1)
                except NoSuchElementException:
                    break
        except Exception as e:
            break    
                #print("end scrolling")
                #break; 
def get_user_details(driver,usr):
    try:
        profile_picture_link = number_posts = number_followers = number_following = user_public_name = user_description = user_other_url=None
        if (len(driver.find_elements(By.XPATH,"//div/span[@class='_2dbep ']/img")) > 0 ):
            profile_picture_link = driver.find_element(By.XPATH,"//div/span[@class='_2dbep ']/img").get_attribute('src')

        if (len(driver.find_elements(By.XPATH,"//ul[@class='k9GMp ']/li/div/span")) > 0 ):
            number_posts = driver.find_element(By.XPATH,"//ul[@class='k9GMp ']/li/div/span").text
            number_posts=int(number_posts.replace('.',''))

        if (len(driver.find_elements(By.XPATH,"//ul[@class='k9GMp ']/li/a[contains(@href,'followers')]/div/span")) > 0 ):
            number_followers = driver.find_element(By.XPATH,"//ul[@class='k9GMp ']/li/a[contains(@href,'followers')]/div/span").get_attribute('title')
            number_followers = int(number_followers.replace('.',''))
        elif (len(driver.find_elements(By.XPATH,"//ul[@class='k9GMp ']/li/div[text()[contains(., 'followers')]]/span")) > 0) :
            number_followers = driver.find_element(By.XPATH,"//ul[@class='k9GMp ']/li/div[text()[contains(., 'followers')]]/span").get_attribute('title')
            number_followers = int(number_followers.replace('.',''))
        else:
            number_followers = None

        if (len(driver.find_elements(By.XPATH,"//ul[@class='k9GMp ']/li/a[contains(@href,'following')]/div/span")) > 0 ):
            number_following = driver.find_element(By.XPATH,"//ul[@class='k9GMp ']/li/a[contains(@href,'following')]/div/span").text
            number_following = int(number_following.replace('.',''))
        elif (len(driver.find_elements(By.XPATH,"//ul[@class='k9GMp ']/li/div[text()[contains(., 'following')]]/span")) > 0):
            number_following = driver.find_element(By.XPATH,"//ul[@class='k9GMp ']/li/div[text()[contains(., 'following')]]/span").text
            number_following = int(number_following.replace('.',''))
        else:
            number_following = None

        if (len(driver.find_elements(By.XPATH,"//div[@class='QGPIr']/span")) > 0 ):
            user_public_name = driver.find_element(By.XPATH,"//div[@class='QGPIr']/span").text

        if (len(driver.find_elements(By.XPATH,"//div[@class='QGPIr']/div")) > 0 ):
            user_description = driver.find_element(By.XPATH,"//div[@class='QGPIr']/div").text

        if (len(driver.find_elements(By.XPATH,"//div[@class='QGPIr']/a")) > 0 ):
            user_other_url = driver.find_element(By.XPATH,"//div[@class='QGPIr']/a").get_attribute('href')        

        img = Image(image_link=profile_picture_link, user = usr, image_type=Catalog.objects.get(variable = "PROFILE_PICTURE"))
        img.save_image()
    
        usr.number_posts = number_posts
        usr.number_followers = number_followers
        usr.number_following = number_following
        usr.user_public_name = user_public_name
        usr.user_description = user_description
        usr.user_other_url = user_other_url
        
        usr.save_user()

    except NoSuchElementException as err :
        print(err)

def scrape_page(driver):
    
    body = driver.execute_script("return document.body")
    source = body.get_attribute('innerHTML') 
    soup = BeautifulSoup(source, "html.parser")
    return soup

def get_publication_details(driver, post):
    try:
        picture_link = number_likes = publication_date = None

        if (len(driver.find_elements(By.XPATH,"//div[@class='eLAPa kPFhm']//img")) > 0 ):
            picture_link = driver.find_element(By.XPATH,"//div[@class='eLAPa kPFhm']//img").get_attribute('src')

        if (len(driver.find_elements(By.XPATH,"//div[@class ='_7UhW9   xLCgt        qyrsm KV-D4               fDxYl    T0kll ']/span")) > 0 ):
            number_likes = driver.find_element(By.XPATH,"//div[@class ='_7UhW9   xLCgt        qyrsm KV-D4               fDxYl    T0kll ']/span").text
            number_likes = int(number_likes.replace('.',''))
        else:
            number_likes = 0

        if (len(driver.find_elements(By.XPATH,"//time[@class='_1o9PC']")) > 0 ):
            format_data = "%Y-%m-%dT%H:%M:%S.%fZ"
            publication_date = driver.find_element(By.XPATH,"//time[@class='_1o9PC']").get_attribute("datetime")
            publication_date  = datetime.strptime(publication_date, format_data)  

        img = Image(image_link=picture_link, user = post.user, publication=post,image_type=Catalog.objects.get(variable = "POST_PICTURE"))
        img.save_image()


        post.number_likes= number_likes
        post.publication_date = publication_date

        post.save_publication()
            
    except Exception as err:
        print(err)
#Aqui empieza el codigo de Imagenes

#Main2 es analisis de imagenes
def main2():
    #Aqui va el codigo de Sebastian y Diego
    srute = pathlib.Path().absolute()
    drute = str(srute)
    cadena = drute.replace("\\", "/")
    face_cascade=cv2.CascadeClassifier( cadena + '/xml/haarcascade_frontalface_default.xml')
    #Se detecta los ojos dentro del rostro a partir de un xml con ruta oabsoluta
    eye_cascade=cv2.CascadeClassifier( cadena + '/xml/haarcascade_eye.xml')
    #Se detecta los anteojos dentro del rostro a partir de un xml con ruta oabsoluta
    eyeg_cascade=cv2.CascadeClassifier( cadena + '/xml/haarcascade_eye_tree_eyeglasses.xml')
    #Se detecta los anteojos dentro del rostro a partir de un xml con ruta oabsoluta
    smile_cascade=cv2.CascadeClassifier( cadena + '/xml/haarcascade_smile.xml')
    #Detector Entrenado
    train_cascade=cv2.CascadeClassifier( cadena + '/classifier/cascade.xml')

    #Metodo detector de texto
    lectorTexto = easyocr.Reader(["es"], gpu=False)
    final_size = 1200
    z = 0
    aux = 0
    with open('navigate_publicationPrueba.csv') as File:
        reader = csv.reader(File, delimiter=',', quotechar=',',
                        quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            url = str(row)
            url1 = url.split(';')
            scomas = url1[1].replace("'","")
            llave = scomas.replace("]","")
            llave2 = int(llave.replace(" ",""))
            if llave2 != aux or z == 0:
                
                llave3 = str(llave2)
                os.chdir(cadena + '/images/Directorio/')
                if os.path.exists('carpeta' + llave3):
                    #print("Ya existe")
                    path = cadena + '/images/Directorio/carpeta' + llave3 +'/images/'
                    dirs = os.listdir(path)
                    pathf= cadena + '/images/Directorio/carpeta' + llave3 + '/images1200/'
                    dirsf = os.listdir(pathf)
                    pathValida= cadena + '/images/Directorio/carpeta' + llave3 + '/imgValidas/'
                    pathNoValidas = cadena + '/images/Directorio/carpeta' + llave3 + '/imgNoValidas/'
                    path5050 = cadena + '/images/Directorio/carpeta' + llave3 + '/img5050/'
                    def resize():
                        for item in dirs:
                            if os.path.isfile(path+item):
                                im = Image.open(path+item)
                                f, e = os.path.splitext(pathf+item)
                                size = im.size
                                ratio = float(final_size) / max(size)
                                new_image_size = tuple([int(x * ratio) for x in size])
                                im = im.resize(new_image_size, Image.ANTIALIAS)
                                new_im = Image.new("RGB", (final_size, final_size))
                                new_im.paste(im, ((final_size - new_image_size[0]) // 2, (final_size - new_image_size[1]) // 2))
                                new_im.save(f + 'resized.jpg', 'JPEG', quality=90)

                    def analisis():
                        for itemf in dirsf:
                            print("Entro al for")
                            if os.path.isfile(pathf+itemf):
                                print("Entro al if")
                                imgf = cv2.imread(pathf+itemf)
                                # Se obtiene en escala de grises
                                gray = cv2.cvtColor(imgf, cv2.COLOR_BGR2GRAY)
                                rostro = train_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=50, minSize=(95, 300))

                                # Deteccion de rostros
                                faces = face_cascade.detectMultiScale(gray, 1.3, 5)  # Imgen gris, Factor de Escala, Vecinos Minimos
                                a_train = None
                                b_train = None
                                face_var = None
                                smile_var = None
                                for (x, y, w, h) in faces:
                                    # Dibuja un rectangulo en en rostro
                                    face_var = cv2.rectangle(imgf, (x, y), (x + w, y + h), (255, 0, 0),2)  # Imagen, El punto de inicio, El color del rectangulo, Espesor del reactangulo
                                    # Recorte de la imagen  en el filtro de grises donde se detecta el rostro
                                    roi_gray = gray[y:y + h, x:x + w]
                                    roi_color = imgf[y:y + h, x:x + w]

                                    # Se detectan los ojos
                                    eyes = eye_cascade.detectMultiScale(roi_gray, 1.2, 5)
                                    # Para cada ojo
                                    for (ex, ey, ew, eh) in eyes:
                                        cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (178, 255, 40),
                                                    2)  # Imagen, El punto de inicio, El color del rectangulo, Espesor del reactangulo

                                    # Se detectan la sonrisa
                                    smile = smile_cascade.detectMultiScale(roi_gray, 1.2, 50)
                                    # Para cada ojo
                                    for (sx, sy, sw, sh) in smile:
                                        smile_var = cv2.rectangle(roi_color, (sx, sy), (sx + sw, sy + sh), (0, 0, 0),
                                                    2)  # Imagen, El punto de inicio, El color del rectangulo, Espesor del reactangulo

                                    for (x, y, w, h) in rostro:
                                        # Filtro Especifico Cascada
                                        a_train = cv2.rectangle(imgf, (x, y), (x + w, y + h), (255, 178, 215),
                                                                2)  # Imagen, El punto de inicio, El color del rectangulo, Espesor del reactangulo
                                        # Recorte de la imagen  en el filtro de grises donde se detecta el rostro
                                        #b_train = cv2.putText(img, 'Rostro', (x, y - 10), 2, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                                result = lectorTexto.readtext(imgf)
                                a_texto = None
                                for res in result:
                                    # print('result: ',res)
                                    pt0n = res[0][0]
                                    pt1n = res[0][1]
                                    pt2n = res[0][2]
                                    pt3n = res[0][3]
                                    pt0 = list(map(int, pt0n))
                                    pt1 = list(map(int, pt1n))
                                    pt2 = list(map(int, pt2n))
                                    pt3 = list(map(int, pt3n))
                                    a_texto = cv2.rectangle(imgf, pt0, pt2, (0, 0, 255),
                                                                2)  # Imagen, El punto de inicio, El color del rectangulo, Espesor del reactangulo
                                #print(itemf)
                                saveimg = Image.open(pathf+itemf)
                                new_im = Image.new("RGB",(final_size,final_size))
                                new_im.paste(saveimg)
                                if (face_var is None) or (a_texto is not None):
                                    print("Imagen No Valida "+itemf)
                                    new_im.save(pathNoValidas+itemf, 'JPEG', quality=90)
                                    #cv2.imshow('Image '+itemf , imgf)
                                    #cv2.waitKey(0)
                                else:
                                    if ((face_var is None) and (a_train is not None)) or ((face_var is not None) and (a_train is None)):
                                        print("Podria ser Valida "+itemf)
                                        #cv2.imshow('Podria Ser Valida', imgf)
                                        new_im.save(path5050+itemf, 'JPEG', quality=90)
                                        #cv2.waitKey(0)
                                    else:
                                        if((face_var is not None) and (a_train is not None)):
                                            print("Imagen Valida "+itemf)
                                            new_im.save(pathValida+itemf, 'JPEG', quality=90)
                                            #cv2.imshow('Imagen Valida '+itemf, imgf)
                                            #cv2.waitKey(0)
                                        else:
                                            print("Sin categoria")             
                                            #cv2.imshow('Sin categoria', imgf) 
                                            #cv2.waitKey(0)
                    def db():
                        conexion1 = psycopg2.connect(database="mental_data_ig", user="postgres", password="root",port="5433")
                        cursor1=conexion1.cursor()
                        sql1 = "ALTER TABLE IF EXISTS navigate_publication ADD COLUMN IF NOT EXISTS valid_img INT"
                        cursor1.execute(sql1)
                        conexion1.commit()
                        conexion1.close()
                    #print("Empezo resize")
                    resize()
                    #print("Termino resize")
                    #print("Empezo analisis")
                    analisis()
                    #db()
                    print("Termino analisis")
                    aux=llave2
                    z = 1

#Main3 es descarga de imagenes
def main3():
    a = 2
    edgerute = pathlib.Path().absolute()
    edgerutef = str(edgerute)
    
    def download_insta(link):
        driver = webdriver.Edge(executable_path= edgerutef + "\\edgedriver_win64\\msedgedriver.exe", options=edge_options)
        driver.get("https://downloadgram.org/")
        text_box = driver.find_element("name", "url")
        text_box.send_keys(link)

        driver.find_element(By.ID, value='submit').click()
        time.sleep(1)
        try:
            driver.find_element(By.LINK_TEXT, value='DOWNLOAD').click()
            time.sleep(5)
            #print("Descarga exitosa")
            driver.close()
        except:
            #print("page down")
            driver.close()
        return None
    #Rutas
    srute = pathlib.Path().absolute()
    drute = str(srute)
    cadena = drute.replace("\\", "/")
    pathcarpeta = cadena + '/images/Directorio/'
    patheliminar = cadena + '/images/'
    dir = pathcarpeta

    with open('navigate_publicationPrueba.csv') as File:
        reader = csv.reader(File, delimiter=',', quotechar=',',
                        quoting=csv.QUOTE_MINIMAL)
        os.chdir(patheliminar)
        if os.path.exists('Directorio'):
            print("Ya existe Directorio")
            rmtree("Directorio")
        if os.path.exists('Directorio') == False:
            os.mkdir("Directorio")
        for row in reader:
            url = str(row)
            url1 = url.split(';')
            scomas = url1[1].replace("'","")
            scomas2 = url1[0].replace("'","")
            urlf = scomas2.replace("[","")
            llave = scomas.replace("]","")
            llave2 = int(llave.replace(" ",""))
            if llave2 == a:
                print("URL"+llave)
                #Creacion
                b = str(a)
                os.chdir(dir)
                if os.path.exists('carpeta' + b):
                    print("Ya existe")
                else:
                    os.mkdir('carpeta' + b)
                    os.chdir(dir + 'carpeta' + b)
                    os.mkdir('images')
                    os.mkdir('images1200')
                    os.mkdir('img5050')
                    os.mkdir('imgNoValidas')
                    os.mkdir('imgValidas')
                #Ciclo de guardado
                edge_options = Options()
                edge_options.add_experimental_option("prefs", {
                "download.default_directory": drute + "\\images\\Directorio\\carpeta" + b + "\\images\\"})
                download_insta(urlf)
            
            if llave2 != a:
                print("Entra al 2")
                #Salto
                a = a + 1
                b = str(a)
                os.chdir(dir)
                #Nueva creacion de carpeta
                if os.path.exists('carpeta' + b):
                    print("Ya existe en ciclo 2")
                else:
                    os.mkdir('carpeta' + b)
                    os.chdir(dir + 'carpeta' + b)
                    os.mkdir('images')
                    os.mkdir('images1200')
                    os.mkdir('img5050')
                    os.mkdir('imgNoValidas')
                    os.mkdir('imgValidas')
                edge_options = Options()
                edge_options.add_experimental_option("prefs", {
                    "download.default_directory": drute + "\\images\\Directorio\\carpeta" + b + "\\images\\"})
                download_insta(urlf)