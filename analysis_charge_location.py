import pandas as pd
import xmltodict
import openpyxl

from tqdm import tqdm
import sys
import requests
import time
from datetime import datetime

import id

class ChargeLocApi:
    '''
    전기차 충전소 위치데이터 추출
    '''
    pollution_url = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo'
    pollution_params = {'serviceKey': id.CHARGE_KEY,
                        'pageNo': '1',
                        'numOfRows': '9999',
                        'period': '5',
                        'zcode': '44'
                        }
    # 카카오 api 호출
    kakao_url = "https://dapi.kakao.com/v2/local/search/address.json"
    kakao_header = {"Authorization":id.KAKAO_KEY}

    df = {"statNm": [],
          "statId": [],
          "chgerId": [],
          "chgerType": [],
          "addr": [],
          "lat": [],
          "lng": [],
          "useTime": [],
          "busiId": [],
          "busiNm": [],
          "busiCall": [],
          "stat": [],
          "statUpdDt": [],
          "powerType": [],
          "zcode": [],
          "parkingFree": [],
          "note": [],
          "bump_dong": [],
          "hang_dong": [],
          }

    colname_conv = {
        "statNm": "충전소명",
        "statId": "충전소ID",
        "chgerId": "충전기ID",
        "chgerType": "충전기타입",
        "addr": "주소",
        "lat": "위도",
        "lng": "경도",
        "useTime": "이용가능시간",
        "busiId": "기관아이디",
        "busiNm": "운영기관명",
        "busiCall": "운영기관연락처",
        "stat": "충전기상태",
        "statUpdDt": "상태갱신일시",
        "powerType": "충전기종류",
        "zcode": "지역코드",
        "parkingFree": "주차료무료여부",
        "note": "충전소안내",
        "bump_dong": "법정동",
        "hang_dong": "행정동",
    }

    # 행정동
    cheonan_dong = {"목천읍", "풍세면", "광덕면", "북면", "성남면", "수신면", "병천면", "동면", "중앙동", "문성동",
                    "원성1동", "원성2동", "봉명동", "일봉동", "신방동", "청룡동", "신안동", "성환읍", "성거읍", "직산읍",
                    "입장면", "성정1동", "성정2동", "쌍용1동", "쌍용2동", "쌍용3동", "백석동", "불당1동", "불당2동", "부성1동",
                    "부성2동"
                    }

    bup_to_hang = {}
    td = datetime.today().strftime('%Y%m%d')

    def __init__(self):
        # 호출
        response = self.try_request("전기차충전", self.pollution_url, self.pollution_params)
        dict_data = xmltodict.parse(response.text)
        rows = dict_data["response"]["body"]["items"]["item"]

        # # 법정동->행정동
        # dong_df = pd.read_excel("do_not_remove/행정동법정동매핑_천안_20220901.xlsx")
        # dong_df = dong_df.dropna(axis='index', how='any', subset=["읍면동명"]).reset_index(drop=True)
        # size = len(dong_df)
        # for i in range(size):
        #       self.bup_to_hang[dong_df["동리명"][i]]=dong_df["읍면동명"][i]

        for row in tqdm(rows):
            if "천안시" in row.get("addr", None):
                tup = self.kakao_api(row["addr"])
                if tup:
                    lat, lng, bump_dong, hang_dong = tup

                    if ((lat in self.df["lat"]) and (lng in self.df["lng"])) or (hang_dong not in self.cheonan_dong):
                        continue
                    row["lat"] = lat
                    row["lng"] = lng
                    row["bump_dong"] = bump_dong
                    row["hang_dong"] = hang_dong

                    for key in self.df:
                        self.df[key].append(row.get(key, None))

        df = pd.DataFrame(self.df)
        df = df.rename(columns=self.colname_conv)
        df.to_csv(f"data_after/전기차충전/{self.td}.csv", index=False, encoding='utf-8')

    def kakao_api(self,addr):
        '''
        카카오 api를 호출한다
        '''
        # response = requests.get(self.kakao_url, headers=self.kakao_header, params = {'query': addr, 'analyze_type':"exact"}).json()
        response = self.try_request("카카오API",self.kakao_url,{'query': addr, 'analyze_type':"exact"},self.kakao_header).json()
        try:
            lat = response["documents"][0]["y"]
            lng = response["documents"][0]["x"]
            bump_dong = response["documents"][0]["address"]["region_3depth_name"]
            hang_dong = response["documents"][0]["address"]["region_3depth_h_name"]
            return (lat,lng,bump_dong,hang_dong)
        except:
            return None

    def try_request(self,nm,url,par,headers=None):
        '''
        request를 수행한다. 실패시 30초 대기 후 다시 시도한다. 총 3회 시도한다
        '''
        for i in range(3):
            try:
                if headers:
                    response = requests.get(url,params=par,headers=headers)
                else:
                    response = requests.get(url, params=par)
                return response
            except:
                if i == 2:
                    sys.exit("3회 시도 실패로 강제종료")
                print(f"{nm} API 연결실패! 30초 후", i + 2, "번째시도")
                time.sleep(30)

    # def get_hang_from_doro(self, search):
    #     '''
    #     도로명주소 api를 이용해 행정동명을 찾는다
    #     '''
    #     if "길" in search:
    #         str_idx = search.index("길")
    #     elif "로" in search:
    #         str_idx = search.index("로")
    #     search = search[:str_idx+1]
    #
    #     doro_url = 'https://business.juso.go.kr/addrlink/addrLinkApi.do'
    #     doro_params = {'confmKey': "devU01TX0FVVEgyMDIyMTEyNTE1NTc0NjExMzI2MDU=",
    #                    "currentPage": 1,
    #                    'countPerPage': 10,
    #                    'keyword': search,
    #                    }
    #     response = requests.get(doro_url, params=doro_params)
    #     # response = self.try_request(doro_url, doro_params)
    #     dict_data = xmltodict.parse(response.text)
    #
    #     try:
    #         return dict_data["results"]["juso"][0]["emdNm"]
    #     except:
    #         return None
    #
    # def get_bumpjung(self, addr):
    #       '''
    #       주소를 입력받아서 행정동을 반환한다
    #       '''
    #       # 행정동이 있는경우
    #       for c_d in self.cheonan_dong:
    #             if c_d in addr:
    #                   return c_d
    #
    #       # 법정동이 있는경우
    #       for bup in self.bup_to_hang:
    #             if bup in addr:
    #                   return self.bup_to_hang[bup]
    #
    #       # # 도로명주소인 경우
    #       # dong = self.get_hang_from_doro(addr)
    #       # if not dong:
    #       #     return None
    #       #
    #       # if dong in self.cheonan_dong:
    #       #     return dong
    #       # else:
    #       #     return self.bup_to_hang[dong]