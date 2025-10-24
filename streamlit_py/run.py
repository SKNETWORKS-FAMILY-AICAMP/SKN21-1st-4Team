# sql문 사용을 위한 import
from ..sql_py import emergency_car as sql_car
from ..sql_py import emergency_ex as sql_ex
from ..sql_py import emergency_faq as sql_faq
from ..sql_py import emergerncy_move as sql_move

# csv data upload를 위한 import
from ..csv_py import emergency_car as csv_car
from ..csv_py import emergency_move as csv_move
from ..csv_py import emergency_ex as csv_ex

def run():
    sql_car.emergency_car_table()
    sql_ex.emergency_ex_table()
    sql_faq.emergency_faq_table()
    sql_move.emergency_move_table()
    csv_car.load_car()
    csv_move.load_move()
    csv_ex.main()