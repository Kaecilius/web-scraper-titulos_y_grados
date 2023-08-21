import requests
import numpy as np
import base64
from bs4 import BeautifulSoup
from anticaptchaofficial.imagecaptcha import *
import os
import pandas as pd
import json

# get image captcha
def getImageCaptcha() -> dict:
    url_image_captcha = "https://constancias.sunedu.gob.pe/imageCaptcha"
    response = requests.get(url_image_captcha)
    cookies = response.cookies.get_dict()
    img = np.frombuffer(response.content, np.uint8)
    imgbase64 = base64.b64encode(img)
    data_image = {
        "image": imgbase64,
        "cookies": cookies
    }
    return data_image

# get token 
def getToken() -> str:
    url_token = "https://constancias.sunedu.gob.pe/verificainscrito"
    response = requests.get( url_token )
    soup = BeautifulSoup( response.content, "html.parser")
    input_tag = soup.find_all("input", {"name":"_token"})[0]
    return  input_tag["value"]

def getListDni() -> list:
    df_dni = pd.read_csv("dni.txt", names=["DNI"])
    dni_list = df_dni.loc[:,"DNI"].to_list()
    return dni_list

# get data with post:
def getConsultaSunedu() -> list:
    # solve image captcha:
    apikey = os.getenv("apikey") # apikey for anticaptcha

    # data variables
    token  = getToken() 
    data   = getImageCaptcha()
    image  = data["image"]
    cookies = data["cookies"]

    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key(apikey)

    # generate image from base64
    with open("images/captcha.jpg", "wb") as f:
        f.write(base64.urlsafe_b64decode(image))

    #Solve image captcha
    captcha_text = solver.solve_and_return_solution("images/captcha.jpg")

    results = []
    if captcha_text != 0:
        # print("captcha text "+captcha_text)
        url_consulta = "https://constancias.sunedu.gob.pe/consulta"
    
        body = {
            "doc" : None,
            "opcion": "PUB",
            "_token": token,
            "captcha":captcha_text
        }

        dnis = getListDni() # read file dni.txt
        
        for dni in dnis:
            body["doc"] = dni
            result = requests.post(url_consulta, data = body, cookies= cookies)

            if result.status_code == 200:
                result_text = result.text
                object_text = json.loads( json.loads(result_text) )
                if len(object_text) > 0:
                    results.append( object_text )
        # result = requests.post(url_consulta, data = body, cookies= cookies)
    else:
        print("task finished with error "+solver.error_code)
    return results

def run():
    arr_data = getConsultaSunedu()
    objects = (pd.DataFrame(data) for data in arr_data)

    df = pd.concat(objects, ignore_index=True)

    select_columns = ["gradTitu", "docuNum", "nombre", "apellidos", "tdOficioFec", "lGradTitu" ]
    df[select_columns].to_csv("export_sunedu.csv", index=False)
    
    print( df[select_columns] )

if __name__ == "__main__":
    run()
