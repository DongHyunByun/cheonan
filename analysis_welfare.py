import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import ssl

import datetime
import time
import sys
import warnings

warnings.filterwarnings(action='ignore')

class CrawlingWelfare:
    service_type_val = {"생활안정": "NB0301", "주거-자립": "NB0302", "보육-교육": "NB0303", "고용-창업": "NB0304",
                    "보건-의료": "NB0305", "행정-안전": "NB0306", "임신-출산": "NB0307", "보호-돌봄": "NB0308",
                    "문화-환경": "NB0309", "농립축산어업": "NB0310"}  # chk-type1
    support_type_val = {"현금": "cash", "현물": "stuff", "이용권": "ticket", "서비스": "service", "기타": "etc"}  # rdo-type1
    apply_type_val = {"온라인신청": "BF0101", "타사이트신청": "BF0102", "방문신청": "BF0103",
                  "기타": "(!BF0101 !BF0102 !BF0103)"}  # rdo-type2

    post_keys = ["chk-type1","rod-type1","rdo-type2"] #상세조회용 키(서비스분야, 지원형태, 신청방법)
    super_url = "https://www.gov.kr"
    main_url = "https://www.gov.kr/portal/rcvfvrSvc/svcFind/svcSearchAll"

    now_d = datetime.datetime.today().strftime("%Y-%m-%d")

    size = 0
    final_return_dict = {
        "상세검색_서비스분야": [],
        "상세검색_지원형태": [],
        "상세검색_신청방법": [],

        "게시글_id": [],
        "게시글_url" : [],
        "제목": [],
        "요약": [],
        "지역상위": [],
        "지역하위": [],

        "지원형태": [],
        "신청기간": [],
        "접수기관": [],
        "전화문의": [],

        "지원대상": [],
        "선정기준": [],
        "지원내용": [],

        "신청기간": [],
        "신청방법": [],
        "제출서류": [],

        "접수기관": [],
        "문의처": [],
        # "사이트주소":None,
        "최종수정일": [],
        "스크랩시간": []
    }
    folder = "보조금24"
    after_folder = f"data_after/{folder}"
    td = datetime.datetime.today().strftime('%Y%m%d')
    ld = (datetime.datetime.today() - datetime.timedelta(days=365*10)).strftime("%Y%m%d")

    def __init__(self):
        df = self.crawling()
        df.to_excel(f"{self.after_folder}/{self.td}.xlsx",index=False,encoding="utf-8-stg")

    def crawling(self):
        for st in self.service_type_val:
            for supt in self.support_type_val:
                for at in self.apply_type_val:
                    page_number=0
                    while(1):
                        url_keys = ["chktype1", "tccd", "meancd","startCount"]
                        url_vals = [self.service_type_val[st], self.support_type_val[supt], self.apply_type_val[at], str(page_number)]
                        url = self.get_url(self.main_url, url_keys, url_vals)

                        page = self.try_request(url)  # get요청 후 응답 수신
                        soup = bs(page.text, "html.parser")
                        posts = set(soup.find_all('a', {"class": "card-title"}))
                        if not posts:
                            break

                        for post in posts:
                            last_url = post["href"]
                            url = self.super_url + last_url
                            print(url)

                            now_dict = {key:None for key in self.final_return_dict.keys()}
                            now_dict = self.get_post_info(url,now_dict)

                            if (not now_dict["최종수정일"]) or (now_dict["최종수정일"].replace("-","") < self.ld):
                                continue

                            now_dict["게시글_url"] = url
                            now_dict["게시글_id"] = str(last_url.split("/")[-1].split("?")[0])
                            now_dict["상세검색_서비스분야"] = st
                            now_dict["상세검색_지원형태"] = supt
                            now_dict["상세검색_신청방법"] = at
                            now_dict["스크랩시간"] = self.now_d

                            for key,val in now_dict.items():
                                self.final_return_dict[key].append(val)
                            self.size+=1
                            print(self.size,"번째", end=" ")
                            print(now_dict)

                        page_number+=12

        return pd.DataFrame(self.final_return_dict)

    def get_url(self,main_url,url_keys,url_vals):
        url = main_url+"?"
        size = len(url_keys)

        for i in range(size):
            url+=url_keys[i]+"="+url_vals[i]
            if i!=size-1:
                url+="&"
        return url

    def replace_text(self,text,remove_text=["\r","\n","\t","\xa0"]):
        '''
        text에 필요없는 remove_text를 제거한다
        '''
        text = text.strip()
        for r in remove_text:
            text = text.replace(r,"")

        text = text.lstrip("-").lstrip("=")
        return text

    def try_request(self,url):
        '''
        request를 수행한다. 실패시 30초 대기 후 다시 시도한다. 총 3회 시도한다
        '''
        for i in range(3):
            try:
                post_page = requests.get(url,verify=ssl.CERT_NONE)
                return post_page
            except:
                print("연결실패! 30초 후",i+2,"번째시도")
                if i == 2:
                    sys.exit("3회 시도 실패로 강제종료")
                time.sleep(30)

    def check_exist(self,now_dict,key,val):
        if val:
            if key=="최종수정일":
                now_dict[key]=self.replace_text(val.text,["최종수정일","\r","\n","\t","\xa0"]).replace(".","-")[:-1]
            elif key=="지역상위":
                a = val.text
                if "/" in a:
                    now_dict["지역상위"], now_dict["지역하위"] = a.split("/")
                    now_dict["지역상위"] = now_dict["지역상위"].strip()
                    now_dict["지역하위"] = now_dict["지역하위"].strip()
                else:
                    now_dict["지역상위"] = a
            else:
                now_dict[key] = self.replace_text(val.text)


    def get_post_info(self,url,now_dict):
        '''
        HTML에서 데이터들의 위치를 확인하고 데이터를 추출한다
        '''
        def get_key_val(post_list):
            for p_l in post_list:
                k = p_l.strong.text
                if k not in now_dict:
                    continue

                type_list = [p_l.span,p_l.pre,p_l.div,]
                for tl in type_list:
                    if tl:
                        v = self.replace_text(tl.text)
                        now_dict[k]=v
                        break

        post_page = self.try_request(url)
        post_soup = bs(post_page.text, "html.parser")

        # ---------영역별 크롤링---------
        self.check_exist(now_dict, "제목", post_soup.find('h2', {"class": "service-title"}))
        self.check_exist(now_dict, "요약", post_soup.find('p', {"class": "service-desc"}))
        self.check_exist(now_dict, "신청기간", post_soup.find('li', {"class": "term"}))
        self.check_exist(now_dict, "전화문의", post_soup.find('li', {"class": "call"}))
        self.check_exist(now_dict, "신청방법", post_soup.find('li', {"class": "method"}))
        self.check_exist(now_dict, "접수기관", post_soup.find('li', {"class": "reception"}))
        self.check_exist(now_dict, "지원형태", post_soup.find('li', {"class": "support"}))
        self.check_exist(now_dict, "최종수정일", post_soup.find('div', {"class": "info-date"}))
        self.check_exist(now_dict, "지역상위", post_soup.find('span', {"class": "chip"})) # 지역

        post1 = post_soup.find_all('ul', {"class": "service-detail-list"})
        get_key_val(post1)

        post2 = post_soup.find_all('div', {"class": "detail-wrap"})
        get_key_val(post2)

        post3 = post_soup.find_all('div', {"class": "warn-title"})
        get_key_val(post3)

        post4 = post_soup.find_all('div', {"class": "detail-box"})
        get_key_val(post4)

        post5 = post_soup.find_all('div', {"class": "datail-wrap"}) # 지원대상용, html상 detail 오타난듯함
        get_key_val(post5)

        return now_dict



