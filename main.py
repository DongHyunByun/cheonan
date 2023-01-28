import argparse

from population import * # 인구데이터 변환
from analysis_welfare import * # 보조금24 크롤링
from analysis_charge_location import * # 보조금24 크롤링
from population_kosis import * # 인구지표

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--type", type=str, default=None,
                      help="수행할 작업, [인구이동통계, 연령별인구현황, 전입전출현황, 보조금24크롤링, 전기차충전소, 인구지표]")
    config = args.parse_args()

    conv_type = config.type

    if conv_type=="인구이동통계": #출생사망현황
        PopulationMove()
    elif conv_type=="연령별인구현황": #연령별인구현황
        PopulationAge()
    elif conv_type=="전입전출현황": #관내이동현황, 관외이동현황
        PopulationInOut()
    elif conv_type=="보조금24크롤링":
        CrawlingWelfare()
    elif conv_type=="전기차충전소":
        ChargeLocApi()
    elif conv_type=="인구지표":
        PopulationKosis()
    else:
        print("작업명령이 잘못되었습니다. 아래의 작업 항목을 정확히 입력하세요")
        print("[인구이동통계, 연령별인구현황, 전입전출현황, 보조금24크롤링, 전기차충전소, 인구지표]")

    print("---------done---------")

