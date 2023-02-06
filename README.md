# cheonan 데이터 솔루션

1. **기간 : 2021.07 ~ 2022.12** 

2. **기술스택**
    1. 개발언어 : python
    2. IDE : pycharm
    3. BeautifulSoup, pandas, kakaoAPI, docker
 
3. **내용**
    1. 카카오API, BeautifulSoup크롤링을 통한 데이터 수집 수행
    2. pandas를 이용한 데이터 전처리
    3. docker를 이용한 데이터 수집, 전처리 소스 이미지 빌드
    4. 로컬의 csv파일을 볼륨바인딩을 통해 이미지의 소스로 읽어서 데이터 처리

4. **파일설명**
    1. *.py : 데이터 크롤링 및 전처리 파일
    2. data_before : 전처리 할 데이터 폴더
    3. data_before : 전처리 후 데이터가 저장될 폴더
    4. Dockerfile : 이미지 빌드용 도커파일
    5. cheonan_deploy : 배포용 폴더, 빌드한 이미지로 로컬에서 처리할 파일을 저장할 폴더
