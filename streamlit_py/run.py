import os
import sys
import subprocess

#프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

#sql문 사용을 위한 import
import sql_py.emergency_car as sql_car
import sql_py.emergency_ex as sql_ex
import sql_py.emergency_faq as sql_faq
import sql_py.emergerncy_move as sql_move 

#csv data upload를 위한 import
import csv_py.emergency_car as csv_car
import csv_py.emergency_move as csv_move
import csv_py.emergency_ex as csv_ex

def run():
    sql_car.emergency_car_table()
    sql_ex.emergency_ex_table()
    sql_faq.emergency_faq_table()
    sql_move.emergency_move_table()
    csv_car.load_car()
    csv_move.load_move()
    csv_ex.main()