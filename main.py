from bs4 import BeautifulSoup
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
from datetime import datetime, timezone
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 允许的 HTTP 方法
    allow_headers=["*"],  # 允许的请求头
)

def fetch_book_details(ISBN,surl,num):
    url = f"http://opac.nlc.cn/F/{surl}-{num}"
    querystring = {
        "find_base": ["NLC01", "NLC09"],
        "func": "find-m",
        "find_code": "ISB",
        "request": ISBN,
        "local_base": "",
        "filter_code_1": "WLN",
        "filter_request_1": "",
        "filter_code_2": "WYR",
        "filter_request_2": "",
        "filter_code_3": "WYR",
        "filter_request_3": "",
        "filter_code_4": "WFM",
        "filter_request_4": "",
        "filter_code_5": "WSL",
        "filter_request_5": ""
    }

    headers = {
        "Date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Host": "opac.nlc.cn",
    }
    
    resp = requests.get(url, headers=headers, params=querystring)
    resp.encoding = 'utf-8'

    main_page = BeautifulSoup(resp.text, 'html.parser')
    alists = main_page.find_all('td', class_='td1')

    def cleaned_data(data):
        return data.replace('\n', '').replace('\xa0', '').replace('/', '').strip()

    book_details = {
        'id': '',
        'name': '',
        'publisher': '',
        'description': '',
        'ISBN': ISBN,
        'author': '',
    }
    temp=False
    temp_name=""
    for i in range(len(alists)):
        if temp and temp_name:
            book_details[temp_name] = cleaned_data(alists[i].text)
            temp=False
            temp_name=''
            continue
        if '题名与责任' in alists[i].text:
            temp=True
            temp_name='name'
        elif 'ID' in alists[i].text:
            temp=True
            temp_name='id'
        elif '一般附注' in alists[i].text or '内容提要' in alists[i].text:
            temp=True
            temp_name='description'

        elif '出版项' in alists[i].text:
            temp=True
            temp_name='publisher'
            
        elif '著者' in alists[i].text:
            temp=True
            temp_name='author'
                
        else:
            temp_name=''
    return {"detail":book_details,"code":200,"ISBN":ISBN}

def fetch_book_url(ISBN):
    url = "http://opac.nlc.cn/F"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Proxy-Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
    }

    resp = requests.request("GET", url, headers=headers)
    resp.encoding = 'utf-8'

    main_page = BeautifulSoup(resp.text, 'html.parser')
    alists=main_page.find_all('a',class_="gblue1")
    for a in alists:
        if(a.text=="多字段检索"):
            pattern = r'/F/([^/-]+)-(\d+)'
            match = re.search(pattern, a.get('href'))
            if match:
                first_part = match.group(1)
                second_part = match.group(2)
                num=int(second_part)-1
                return(fetch_book_details(ISBN,first_part, str(num)))

            else:
                print("没有匹配到结果")

@app.get('/getMes/{ISBN}')
async def get_book_info(ISBN: str):
    book_details = fetch_book_url(ISBN)
    print(book_details)
    if book_details:    
        return book_details
    else:
        return {
            "code":100
        }
@app.get('/')
async def getMes():
    return {"code":200}
if __name__ == '__main__':
    uvicorn.run(app, port=7000)

