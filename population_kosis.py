import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import urllib.request as req
import openpyxl
import sys
import re
from datetime import datetime
import time
from tqdm import tqdm

from tqdm import tqdm

class PopulationKosis:
    refer_file_path = 'do_not_remove/KOSIS_URL2.xlsx'
    td = datetime.today().strftime("%Y%m%d")
    df = pd.DataFrame([], columns=["SEQ", 'TBL_NM', 'PRD_DE', 'TBL_ID', 'ITM_NM', 'ITM_ID', 'ORG_ID', 'UNIT_NM',
                                       'UNIT_NM_ENG', 'C1_OBJ_NM', 'DT', 'PRD_SE', 'C1', 'C1_NM', 'ITM_NM_ENG',
                                       'C1_OBJ_NM_ENG', 'C1_NM_ENG', 'C2_OBJ_NM', 'C2_OBJ_NM_ENG',
                                       'C2', 'C2_NM', 'C2_NM_ENG', 'err', 'errMsg', "REG_DT"])

    def make_df(self,date_list,url):
        for date in date_list:
            url1 = url + '&startPrdDe=' + date + '&endPrdDe=' + date
            res = self.try_request(url1)
            json_obj = json.load(res)
            temp_df = pd.json_normalize(json_obj)
            if (temp_df.columns[0] != 'err'):
                self.df = pd.concat([self.df, temp_df])

    def __init__(self):
        kosis_data = pd.read_excel(self.refer_file_path)
        kosis_data.columns = ['통계표명', '통계표ID', '요청_URL', '수집_날짜', '주기', '업데이트날짜']

        # pre_name = '111'
        for table_name, url, date, date_period in zip(kosis_data['통계표ID'], kosis_data['요청_URL'], kosis_data['수집_날짜'], kosis_data['주기']):
            print(url)
            # 통계표명이 달라질 때 저장
            # if pre_name != table_name:
            #    pre_name = table_name
            #    df.to_csv("C:\\RPA\\kosis\\"+pre_name+".csv", index=False, encoding = 'utf-8-sig')
            #    df = pd.DataFrame([],columns=['TBL_NM', 'PRD_DE', 'TBL_ID', 'ITM_NM', 'ITM_ID', 'ORG_ID', 'UNIT_NM',
            #       'UNIT_NM_ENG', 'C1_OBJ_NM', 'DT', 'PRD_SE', 'C1', 'C1_NM'])

            # 수집날짜 리스트 만들기
            date_input = date.split(' ~ ')
            start_date, end_date = date_input[0], date_input[1]

            end_date = datetime.today().strftime("%Y")
            date_list = []
            if (date_period == 'H'):
                end_date = end_date + "02d"
                for year in range(int(start_date[:4]), int(end_date[:4]) + 1):
                    # for quarter in ['01','02','03','04']:
                    for quarter in ['01', '02']:
                        if year == int(start_date[:4]) and int(quarter) < int(start_date[5]):
                            continue
                        elif year == int(end_date[:4]) and int(quarter) > int(end_date[5]):
                            continue
                        else:
                            date_list.append(str(year) + quarter)
            elif (date_period == 'Y'):
                for year in range(int(start_date), int(end_date) + 1):
                    date_list.append(str(year))
            else:
                continue
            #    for year in range(int(start_date), int(end_date)+1):
            #        if (int(str(year)[-2:]) > 12) or (str(year)[-2:] == '00'):
            #                continue
            #        else:
            #            date_list.append(str(year))

            self.make_df(date_list,url)

            size = len(self.df)
            self.df["REG_DT"] = [self.td for _ in range(size)]
            self.df["SEQ"] = [i for i in range(1, size + 1)]
            self.df.to_excel("data_after/KOSIS인구지표/kosis_data.xlsx", sheet_name='data', index=False)

    def try_request(self,url1):
        '''
        request를 수행한다. 실패시 30초 대기 후 다시 시도한다. 총 3회 시도한다
        '''
        for i in range(3):
            try:
                res = req.urlopen(url1)
                return res
            except:
                if i == 2:
                    sys.exit("3회 시도 실패로 강제종료")
                print("연결실패! 30초 후", i + 2, "번째시도")
                time.sleep(30)

    def make_df(self,date_list,url):
        for date in date_list:
            try:
                url1 = url + '&startPrdDe=' + date + '&endPrdDe=' + date
                res = self.try_request(url1)
                json_obj = json.load(res)
                temp_df = pd.json_normalize(json_obj)
                if (temp_df.columns[0] != 'err'):
                    self.df = pd.concat([self.df, temp_df])
            except:
                pass