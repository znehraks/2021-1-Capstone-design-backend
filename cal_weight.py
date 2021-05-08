from scrapper import scrapper
import json
import csv
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import io
import sys
from operator import itemgetter
from haversine import haversine
import math
# 먼저 학교 이름으로 학교의 중심 위도,경도를 알아오기


# def find_address(univ_name):
#     # 서울소재대학교 주소 csv에서 가져옴
#     univ = open('seoul_universities.csv', 'r')
#     univ_r = csv.reader(univ)
#     # univ_address에 필요한 대학교 주소 데이터 추출
#     univ_address = ""
#     for i in univ_r:
#         if univ_name == i[3]:
#             univ_address = i[8]
#             break
#     univ.close()
#     # print(univ_address)

#     url = f"https://map.naver.com/v5/api/search?caller=pcweb&query={univ_address}"

#     sys.stdout.reconfigure(encoding='utf-8')
#     chrome_options = Options()
#     chrome_options.add_experimental_option(
#         "excludeSwitches", ["enable-logging"])
#     driver = webdriver.Chrome(
#         executable_path=".\\chromedriver.exe", options=chrome_options)

#     driver.get(url)
#     html = driver.page_source
#     soup = BeautifulSoup(html, "lxml")
#     address_json = json.loads(soup.find("body").text)
#     driver.close()
#     return address_json


# def get_address_json(address_json):
#     address_lon = 0
#     address_lat = 0
#     try:
#         address_lon = float(address_json["result"]["place"]["list"][0]["x"])
#         address_lat = float(address_json["result"]["place"]["list"][0]["y"])
#     except:
#         pass

#     if address_lon == 0:
#         try:
#             address_lon = float(
#                 address_json["result"]["address"]["jibunsAddress"]["list"][0]["x"])
#             address_lat = float(
#                 address_json["result"]["address"]["jibunsAddress"]["list"][0]["y"])
#         except:
#             pass
#     if address_lon == 0:
#         try:
#             address_lon = float(
#                 address_json["result"]["address"]["roadAddress"]["list"][0]["x"])
#             address_lat = float(
#                 address_json["result"]["address"]["roadAddress"]["list"][0]["y"])
#         except:
#             pass

#     return(address_lon,  address_lat)
#     # print(address_lat, address_lon)


# 알아 온 위도, 경도를 바탕으로 상하좌우,중심 위도경도를 구함
def get_residence_address(address_lon, address_lat):
    center_lat = address_lat
    center_lon = address_lon
    btm_lat = address_lat - 0.0159
    left_lon = address_lon - 0.0412
    top_lat = address_lat + 0.0159
    right_lon = address_lon + 0.0412

    site_json = scrapper(center_lat, center_lon, btm_lat,
                         left_lon, top_lat, right_lon)

    items = site_json["data"]["ARTICLE"]
    refined_items = []
    for i in items:
        refined_items.append({
            "lgeo": i["lgeo"],
            "count": i["count"],
            "lat": i["lat"],
            "lon": i["lon"]
        })
    return refined_items
# 나온 매물 리스트들 좌표로 각각의 lgeo를 인덱스로 하여
# 그 lego의 lat, lon을 이용한 거리이용 가중치를 모두 구함
# 학교 좌표와 해당 매물과의 거리를 모두 구하여(맨하탄거리) 1위부터 꼴찌까지 가중치를 구함(이전에, Q2의 최대거리에서 필터링하여 해당 거리를 벗어나는 좌표에 있는 항목은 이 단계에서 걸러냄)


def cal_T1(refined_residence, univ_lon, univ_lat, limit_dist):
    limit_dist = float(limit_dist)
    # 직선거리로 이루어진 배열 생성 후 저장
    loc = []
    # abs(i["lat"]-univ_lat)+abs(i["lon"]-univ_lon)
    for i in refined_residence:
        loc.append({"lgeo": i["lgeo"], "dist": haversine(
            (i["lat"], i["lon"]), (univ_lat, univ_lon), unit='m'), "lat": i["lat"], "lon": i["lon"],
            "count": i["count"]})

    # 가까운 순으로 정렬
    sorted_loc = sorted(
        loc, key=itemgetter('dist'))

    # limit_dist를 벗어나는 매물 제거
    sorted_loc_filtered = []
    for index, i in enumerate(sorted_loc):
        if sorted_loc[index]["dist"] <= limit_dist:
            sorted_loc_filtered.append(i)
        else:
            break

    # 직선거리로 서열을 매겨 총 개수로 나눈 후 100점 만점(1위) 부터 0점까지(꼴찌) 1위부터 높은 점수로 배열함
    # ex.총 매물이 50일 경우, 1위가 100점, 2위가 98점, 3위가 96점 ... 50위가 0점 (동률에 대한 고려는 추후에 함)
    res = []
    len_sorted_loc_filtered = len(sorted_loc_filtered)
    # print(len_sorted_taxicab_geom)
    for index, i in enumerate(sorted_loc_filtered):
        res.append({"lgeo": i["lgeo"],
                    "count": i["count"], "dist": i["dist"], "lat": i["lat"], "lon": i["lon"],
                    "T1_weight": 100*(1/len_sorted_loc_filtered)*(len_sorted_loc_filtered-index)})
    return res

# 각 매물에서 해당 구에 속한 지하철역중 가장 가까운 것의 거리를 가중치로 매겨서 그것 역시 1위부터 꼴찌까지 가중치로 매김


def cal_T2(refined_residence):
    # 각각의 매물이 어느 지하철역이랑 가깝고(1개) 얼마나 가까운지 맨하탄거리로 표시
    # 지하철csv 불러옴
    subway = open('subway_refined.csv', 'r')
    subway_r = csv.reader(subway)
    subway_r_list = list(subway_r)
    # 중간결과를 담을 subway_list 생성
    subway_list = []

    # 매물리스트를 outer에 지하철리스트를 inner에 두고 각 매물에서 모든 지하철역과의 거리를 계산하여
    # 가장 가까운 지하철 역과 그 역과의 거리를 구함
    for index_r, i in enumerate(refined_residence):
        # 임시로 매물과 모든역과의 거리를 계산할 리스트
        temp = []
        for index_s, j in enumerate(subway_r_list):
            if(index_s == 0):
                continue
            temp.append(abs(i["lat"] - float(j[7])) +
                        abs(i["lon"] - float(j[8])))
            if(index_s == len(subway_r_list)-1):
                subway_list.append({"lgeo": i["lgeo"], "nearest": temp.index(
                    min(temp))+1, "subway_dist": min(temp)})

    subway.close()
    # 거리가 가까운 순으로 정렬함
    sorted_subway_list = sorted(
        subway_list, key=itemgetter('subway_dist'))

    # 최종결과를 담을 리스트 생성
    res = []

    len_sorted_subway_list = len(sorted_subway_list)

    # T2최종 가중치 추산을 위한 계산작업
    for index, i in enumerate(sorted_subway_list):
        res.append({"lgeo": i["lgeo"], "nearest": i["nearest"], "subway_dist": i["subway_dist"],
                    "T2_weight": 100*(1/len_sorted_subway_list)*(len_sorted_subway_list-index)})
    return res

    # 맨하탄거리로 서열을 매겨 총 개수로 나눈 후 100점 만점(1위) 부터 0점까지(꼴찌) 1위부터 높은 점수로 배열함
    # ex.총 매물이 50일 경우, 1위가 100점, 2위가 98점, 3위가 96점 ... 50위가 0점 (동률에 대한 고려는 추후에 함)


# 각 매물이 속한 구별 물가로 가중치 합산함
def cal_T3(refined_residence):
    # 물가 csv 불러옴
    price = open('price_refined.csv', 'r')
    price_r = csv.reader(price)
    price_r_list = list(price_r)
    # 중간결과 담을 리스트
    price_list = []

    # 매물리스트를 outer에 지하철리스트를 inner에 두고 각 매물에서 모든 구 와의 거리를 계산하여
    # 가장 가까운 구와 그 구와의 거리를 구함
    for index_r, i in enumerate(refined_residence):
        # 임시로 구와 모든매물과의 거리를 계산할 리스트
        temp = []
        for index_p, j in enumerate(price_r_list):
            if(index_p == 0):
                continue
            temp.append(abs(i["lat"] - float(j[5])) +
                        abs(i["lon"] - float(j[6])))
            if(index_p == len(price_r_list)-1):
                price_list.append({"lgeo": i["lgeo"], "nearest": temp.index(
                    min(temp))+1, "gu_dist": min(temp)})

    price.close()
    # 거리가 가까운 순으로 정렬함
    sorted_price_list = sorted(
        price_list, key=itemgetter('gu_dist'))

    # 최종결과를 담을 리스트 생성
    res = []

    len_sorted_price_list = len(sorted_price_list)

    # T3최종 가중치 추산을 위한 계산작업
    for index, i in enumerate(sorted_price_list):
        res.append({"lgeo": i["lgeo"], "nearest": i["nearest"], "gu_dist": i["gu_dist"],
                    "T3_weight": int(price_r_list[int(i["nearest"])][4])})
    return res

# 구 별 범죄율로 가중치 구함(위도,경도 값으로 해당 점이 어느 구에 속하는지 판별 후, 그 구의 범죄율 가중치로 정함)


def cal_T4(refined_residence):
     # 범죄율 csv 불러옴
    crime = open('crime_refined.csv', 'r')
    crime_r = csv.reader(crime)
    crime_r_list = list(crime_r)
    # 중간결과 담을 리스트
    crime_list = []

    # 매물리스트를 outer에 지하철리스트를 inner에 두고 각 매물에서 모든 구 와의 거리를 계산하여
    # 가장 가까운 구와 그 구와의 거리를 구함
    for index_r, i in enumerate(refined_residence):
        # 임시로 구와 모든매물과의 거리를 계산할 리스트
        temp = []
        for index_c, j in enumerate(crime_r_list):
            if(index_c == 0):
                continue
            temp.append(abs(i["lat"] - float(j[3])) +
                        abs(i["lon"] - float(j[4])))
            if(index_c == len(crime_r_list)-1):
                crime_list.append({"lgeo": i["lgeo"], "nearest": temp.index(
                    min(temp))+1, "gu_dist": min(temp)})

    crime.close()
    # 거리가 가까운 순으로 정렬함
    sorted_crime_list = sorted(
        crime_list, key=itemgetter('gu_dist'))

    # 최종결과를 담을 리스트 생성
    res = []

    len_sorted_crime_list = len(sorted_crime_list)

    # T4최종 가중치 추산을 위한 계산작업
    for index, i in enumerate(sorted_crime_list):
        res.append({"lgeo": i["lgeo"], "nearest": i["nearest"], "gu_dist": i["gu_dist"],
                    "T4_weight": int(crime_r_list[int(i["nearest"])][1])})
    return res

# 매물 수로 난도 가중치를 구함(나온 refined_items의 count가 많은 것 순으로 높은 점수를 매겨서 등수 별로 순차적인 가중치를 정함
# 예. 매물이 총 50개이면 1위 100점, 2위 98점, 3위 96점 ... 50위 0점)


def cal_T5(refined_residence):
    sorted_count_list = sorted(
        refined_residence, key=itemgetter('count'), reverse=True)

    # 최종결과를 담을 리스트 생성
    res = []

    len_sorted_count_list = len(sorted_count_list)

    # T4최종 가중치 추산을 위한 계산작업
    for index, i in enumerate(sorted_count_list):
        res.append({"lgeo": i["lgeo"], "count": i["count"],
                    "T5_weight": 100*(1/len_sorted_count_list)*(len_sorted_count_list-index)})
    return res


# 모든 매물의 점수에 가중치를 곱하여 환산한 최종 값을 구한다.
def get_final_weight(T1, T2, T3, T4, T5, w1, w2, w3, w4, w5):
    # lgeo 별로 lgeo 순으로 정렬,
    sorted_T1 = sorted(T1, key=itemgetter('lgeo'))
    sorted_T2 = sorted(T2, key=itemgetter('lgeo'))
    sorted_T3 = sorted(T3, key=itemgetter('lgeo'))
    sorted_T4 = sorted(T4, key=itemgetter('lgeo'))
    sorted_T5 = sorted(T5, key=itemgetter('lgeo'))

    # T1,T2,T3,T4,T5 모두 더함
    res = []
    for i in range(0, len(sorted_T1)):
        res.append({
            "lgeo": sorted_T1[i]["lgeo"],
            "T1": round(sorted_T1[i]["T1_weight"]*float(w1)/100),
            "T2": round(sorted_T2[i]["T2_weight"]*float(w2)/100),
            "T3": round(sorted_T3[i]["T3_weight"]*float(w3)/100),
            "T4": round(sorted_T4[i]["T4_weight"]*float(w4)/100),
            "T5": round(sorted_T5[i]["T5_weight"]*float(w5)/100),
            "total_weight": round(sorted_T1[i]["T1_weight"]*float(w1)/100 +
                                  sorted_T2[i]["T2_weight"]*float(w2)/100 +
                                  sorted_T3[i]["T3_weight"]*float(w3)/100 +
                                  sorted_T4[i]["T4_weight"]*float(w4)/100 +
                                  sorted_T5[i]["T5_weight"]*float(w5)/100),
            "lat": sorted_T1[i]["lat"],
            "lon": sorted_T1[i]["lon"],
        })
    # total 내림차순으로 sorting함
    res_2 = []
    res_sorted = sorted(res, key=itemgetter('total_weight'), reverse=True)
    for index, i in enumerate(res_sorted):
        res_2.append({
            "rank": index+1,
            "lgeo": i["lgeo"],
            "T1": i["T1"],
            "T2": i["T2"],
            "T3": i["T3"],
            "T4": i["T4"],
            "T5": i["T5"],
            # "fixed_T1": round(i["T1"]*(100/i["total_weight"]), 1),
            # "fixed_T2": round(i["T2"]*(100/i["total_weight"]), 1),
            # "fixed_T3": round(i["T3"]*(100/i["total_weight"]), 1),
            # "fixed_T4": round(i["T4"]*(100/i["total_weight"]), 1),
            # "fixed_T5": round(i["T5"]*(100/i["total_weight"]), 1),
            "total_weight": i["total_weight"],
            "lat": i["lat"],
            "lon": i["lon"],
        })
    #
    return res_2

# TOP3 골라서 이 주변 정보들 가져옴


def filter_top5(total):
    # 5개 추려서 위도, 경도 가져옴
    top5 = []
    for index, i in enumerate(total):
        if index == 5:
            break
        top5.append(i)
    # 그 위도,경도로 주변 근린시설 정보까지 조합하여 반환

    return top5

# 이 Top에 포함되는 항목의 구체적인 정보 서술 및 시각화 => 는 아마 프론트에서
# 지도에 마크로 표시해주는 방법도 좋으리라 생각함 + 매물 및 동네의 추가 정보까지 제공 => 는 아마 프론트에서


# 안씀 address_json = find_address(sys.argv[1])
# 안씀 (univ_lon, univ_lat) = get_address_json(address_json)

# univ_name = sys.argv[1]
# univ_lat = float(sys.argv[2])
# univ_lon = float(sys.argv[3])
# limit_dist = float(sys.argv[4])
# w1 = sys.argv[5]
# w2 = sys.argv[6]
# w3 = sys.argv[7]
# w4 = sys.argv[8]
# w5 = sys.argv[9]

univ_name = "한성대학교"
univ_lat = 37.5825084
univ_lon = 127.0102929
limit_dist = 1795
w1 = "25.5"
w2 = "30"
w3 = "5"
w4 = "20"
w5 = "19.5"

refined_residence = get_residence_address(univ_lon, univ_lat)
T1 = cal_T1(refined_residence, univ_lon, univ_lat, limit_dist)
T2 = cal_T2(T1)
T3 = cal_T3(T1)
T4 = cal_T4(T1)
T5 = cal_T5(T1)
total = get_final_weight(T1, T2, T3, T4, T5, w1, w2, w3, w4, w5)
top5 = filter_top5(total)

top5 = json.dumps(top5)
print(top5)
# print(limit_dist)
# print(weightcode)

# result = json.dumps(total)

# print(len(T1))
# print(len(T2))
# print(len(T3))
# print(len(T4))
# print(len(T5))
# for i in refined_residence:
#     print(i)

# for i in T1:
#     print(i)

# for i in T2:
#     print(i)

# for i in T3:
#     print(i)

# for i in T4:
#     print(i)

# for i in T5:
#     print(i)
# print(total)
# print(refined_residence)
