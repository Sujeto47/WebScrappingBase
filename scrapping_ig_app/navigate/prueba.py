import json
import re
import requests
from bs4 import BeautifulSoup as bs
urlimage='https://www.instagram.com/p/Cg51R_Mum3T/'

descargar=(urlimage)
def descargar(urlimage):
    headers= {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}
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
    print ('Proceso Finalizado')
##########################################################

