import pandas as pd
import numpy as np
import os
import openpyxl
import ssl
import sys

import requests
from urllib import request
from bs4 import BeautifulSoup as bs

class PopulationMove:
    '''
    인구이동통계 데이터 변환.
    데이터의 년,월을 입력받아야 한다.
    '''
    folder = "인구이동통계"
    before_folder = f"data_before/{folder}"
    after_folder = f"data_after/{folder}"
    year = None

    def __init__(self):
        self.year = input("년입력(yyyy) : ")
        self.month = input("월입력(MM) : ")
        d=f"{self.year}-{self.month}"

        sample_file = f"do_not_remove/인구이동통계 샘플양식.xlsx"

        files = os.listdir(self.before_folder)
        df = pd.DataFrame()
        is_file=False

        for file in files:
            if (self.month in file) and (self.month) in file:
                is_file=True
                print(file)
                df = pd.concat([df, self.data_trans(self.before_folder + "/" + file, sample_file, d)])

        if is_file:
            df.to_excel(f"{self.after_folder}/변환후_인구이동통계_{self.year}년_{self.month}월.xlsx", index=False)
        else:
            print(f"변환할 파일({self.year}년 {self.month}월)없음")

    def data_trans(self, down_file, sample_file, date):
        def drop_comma(s):
            return s.replace(",", "")
        # 파일 다운
        down_df = pd.read_excel(down_file)
        sample_df = pd.read_excel(sample_file)

        # 데이터 자르기
        down_df = down_df.iloc[3:, 6:].T.reset_index()
        down_df = down_df.drop(["index"], axis=1)

        # 기준일 칼럼 추가
        size = len(down_df)
        date_df = pd.DataFrame({"기준일": [date for _ in range(size)]})
        down_df = pd.concat([date_df, down_df], axis=1)

        # 샘플데이터 컬럼 붙이기(컬럼 순서가 바뀐다면 수정해야 한다)
        clean_columns = []
        for col in sample_df.columns:
            col = col.rstrip("\t").rstrip(".1")
            clean_columns.append(col)
        down_df.columns = clean_columns

        # 결측치 제거
        down_df = down_df.dropna(axis=0)
        #     display(down_df)

        # 숫자형식으로 바꾸기
        for col in down_df.columns[2:]:
            down_df[col] = down_df[col].apply(drop_comma).astype("int")

        return down_df

class PopulationAge:
    '''
    연령별인구현황 데이터 변환.
    데이터를 크롤링한후 변환을 수행한다.
    '''
    folder = "연령별인구현황"
    before_folder = f"data_before/{folder}"
    after_folder = f"data_after/{folder}"
    year = None
    month = None
    title = None
    real_file_name = None

    def __init__(self):
        self.year = input("월입력(YYYY) : ")
        self.month = input("월입력(M) : ")
        self.title = f"［{self.year}년］{self.month}월말 인구 현황"

        self.crawling_population_age()
        self.data_trans_population_age()


    def crawling_population_age(self):
        '''
        게시글을 크롤링 한다
        '''
        def get_soup(url):
            page = requests.get(url, verify=False)
            return bs(page.text, "html.parser")

        # 게시글 찾기
        main_url = "https://www.cheonan.go.kr"
        list_url = "https://www.cheonan.go.kr/cop/bbs/BBSMSTR_000000001101/selectBoardList.do?bbsId=BBSMSTR_000000001101&pageIndex=1&kind=&searchCnd=&searchWrd="

        list_soup = get_soup(list_url)
        links = list_soup.find_all("span", {"class": "link"})

        is_file = False
        for l in links:
            if self.title in l.text.lstrip().rstrip():
                post_url_right = l.a["href"]
                is_file = True

        if is_file:
            # 첨부파일 찾기
            post_url = main_url + post_url_right
            post_soup = get_soup(post_url)
            attach_files = post_soup.find_all("a", {"class": "mimetype xlsx"})
            for a_f in attach_files:
                file_name = a_f.text.lstrip().rstrip()
                if "연령별인구현황" in file_name:
                    print(f"크롤링 완료 : {file_name}")
                    self.real_file_name = file_name
                    start_i = a_f["href"].index("(")
                    params = a_f["href"][start_i + 1:-1]
                    first_param = params.split(",")[0][1:-1]
                    second_param = params.split(",")[1][1:-1]

                    request.urlretrieve(
                        f"https://www.cheonan.go.kr/cmm/fms/FileDown.do?atchFileId={first_param}&fileSn={second_param}",
                        f"{self.before_folder}/{self.real_file_name}")
        else:
            print("게시물없음")
            sys.exit()

    def data_trans_population_age(self):
        month = self.month.zfill(2)
        raw_df = pd.read_excel(f"{self.before_folder}/{self.real_file_name}", sheet_name="3. 읍면동별 연령별(5세-세로형)")

        # 데이터프레임 만들기
        df1 = raw_df.iloc[1:, [0, 1, 2]].reset_index().drop("index", axis=1)
        df2 = raw_df.iloc[1:, [7 * i + 4 for i in range(21)]].reset_index().drop("index", axis=1)
        df_date = pd.DataFrame({"기준일": [f"{self.year}년 {month} 월" for _ in range(len(df1))]}).reset_index().drop(
            "index", axis=1)
        df = pd.concat([df_date, df1, df2], axis=1, ignore_index=True)

        # 컬럼만들기
        cols = list(df.loc[0])
        cols[0] = "기준일"
        cols[1] = "읍면동"
        cols[2] = "구분"
        df = df.iloc[1:]
        df.columns = cols

        now_loc = ""
        for i in range(1, len(df) + 1):
            if type(df["읍면동"][i]) is str:
                now_loc = df["읍면동"][i].replace(" ", "")
                df["읍면동"][i] = now_loc
            else:
                df["읍면동"][i] = now_loc

        df = df[(df["읍면동"] != "천안시") &
                (df["읍면동"] != "동남구") &
                (df["읍면동"] != "서북구")]

        print(f"파일 변환 완료 : 변환후_{self.real_file_name}")
        df.to_excel(f"{self.after_folder}/변환후_{self.real_file_name}", index=False)

class PopulationInOut:
    folder = "전입전출현황"
    before_folder = f"data_before/{folder}"
    after_folder = f"data_after/{folder}"


    def __init__(self):
        files = os.listdir(self.before_folder)
        self.year = input("년입력(yyyy) : ")
        self.month = input("월입력(M) : ")
        is_file=False
        for file in files:
            if (self.year in file) and (self.month in file):
                is_file=True
                df = pd.read_excel(os.path.join(self.before_folder, file))
                df = df.astype(str)

                print(f"변환완료 : 변환후_{file}")
                df.to_excel(f"{self.after_folder}/변환후_{file}", index=False)

        if not is_file:
            print("변환할 파일 없음")