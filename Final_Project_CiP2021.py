"""
Final Project for the course "Code in Place 2021"
This program can read the Covid-19 data published daily by the Italian Dipartimento di protezione civile.
The user can choose between different sets of data. The chosen set is then printed out in the terminal
and the data are represented on a map of Italy.
Created by Massimiliano Prior, published on June 5th, 2021.
"""

from PIL import Image, ImageDraw
from datetime import date, datetime
import pytz
import requests
from io import BytesIO
import csv

MAP_WIDTH = 930
MAP_HEIGHT = 1096
MIN_LONGITUDE = 6.5272658
MAX_LONGITUDE = 18.7102470232
MIN_LATITUDE = 36.689987291
MAX_LATITUDE = 47.3051462
PROV_DATA_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province-latest.csv"
REG_DATA_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-latest.csv"
REG_DATA_PREFIX = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-"
MAP_URL = "https://raw.githubusercontent.com/makkusu89/codeinplace_final/main/italy.png"
MIN_DATE = [2020, 2, 24]


def main():
    #assigning y to rerun to allow the first run of the program
    #and just an empty string to selection
    rerun = "y"
    intro()
    while rerun == "y":
        response = requests.get(MAP_URL)
        italy_map = Image.open(BytesIO(response.content))
        selection = select()
        if selection == "p":
            run_province(italy_map)
        if selection == "r":
            run_region(italy_map)
        rerun = run_again()


def intro():
    #Just a nice introduction. It won't be repeated when the program is run again.
    print()
    print("                     -----------------------------------------")
    print("                     |      ITALY'S COVID-19 INFECTIONS      |")
    print("                     |        GRAPHICAL REPRESENTATION       |")
    print("                     -----------------------------------------")
    print()
    print("Welcome, this program allows to create graphical representations of the Covid-19 cases in Italy.")
    print("The selected dataset will be printed here and then represented graphically over a pre-existing map of the country.")


def select():
    #Allows selection between two different kinds of datasets.
    #Selecting Regions will lead to a second selection afterwards (more data are available for regions).
    print()
    print("===========================================================================================")
    print()
    selection = input("Type 'p' to see the report sub-divided by province, type 'r' to see it divided by region: ")
    while selection != "p" and selection != "r":
        print()
        print("You can only enter 'p' for the provinces or 'r' for the regions: ")
        selection = input("Please, choose one of the two options reported above: ")
    return selection

###############################################
##            PROVINCE'S DATA                ##
###############################################


def run_province(italy_map):
    #starting the run for provinces, data are gathered from a link stored in a constant
    print("-------------------------------------------------------------------------")
    print()
    print("You chose to see the data divided by province, here is the complete list:")
    print()
    raw_data_prov = requests.get(PROV_DATA_URL).text.splitlines()
    print_provinces(italy_map, raw_data_prov)
    italy_map.show()


def print_provinces(italy_map, raw_data_prov):
    #the following value is used to normalize the data to the maximum value and print the dots based on it
    max_value = find_max(raw_data_prov)
    print()
    #provinces data are read one at a time and the data are directly used to print the corresponding dot on the map
    reader = csv.DictReader(raw_data_prov)
    for line in reader:
        if line["sigla_provincia"] != "":
            latitude = float(line["lat"])
            longitude = float(line["long"])
            positives = float(line["totale_casi"])
            print_dot(italy_map, latitude, longitude, positives, max_value)


def find_max(raw_data_prov):
    #this function reads and prints the data to the terminal.
    #while reading and printing the data, every time a value higher than the previous is found,
    #it is stored in a variable
    max_province = region = ""
    undet_cases = maximum_prov = regional_total = 0
    reader = csv.DictReader(raw_data_prov)
    for line in reader:
        if region != line["denominazione_regione"]:
            print("REGION: " + line["denominazione_regione"])
            print()
        regional_total += int(line["totale_casi"])
        if line["sigla_provincia"] != "":
            #since some data are regularly not assigned to any of the provinces directly, this condition allows to treat
            #these values as a special case.
            region = line["denominazione_regione"]
            temp_value_prov = int(line["totale_casi"])
            if temp_value_prov > maximum_prov:
                maximum_prov = temp_value_prov
                max_province = line["denominazione_provincia"]
            print("In the province of " + line["denominazione_provincia"] + " there have been " + str(line["totale_casi"]) + " cases.")
        elif line["denominazione_provincia"] == "Fuori Regione / Provincia Autonoma":
            undet_cases += float(line["totale_casi"])
            print(line["denominazione_regione"] + " residents found positive outside of the region: " + line["totale_casi"])
            print("The total amount of cases for the region " + line["denominazione_regione"] + " is " + str(regional_total))
        else:
            undet_cases += float(line["totale_casi"])
            print("Cases still to be assigned in the region " + line["denominazione_regione"] + ": " + line["totale_casi"])
            print("-----------------------------------------------------------------")
            print()
            regional_total = 0
    print("Total cases outside of the regions or still to be assigned: ", str(undet_cases))
    print("The highest no. of cases throughout all provinces is found in the province of " + max_province + ": " + str(maximum_prov) + " cases")
    return maximum_prov

###############################################
##              REGIONAL DATA                ##
###############################################


#Allows selection between total values up to date or a single day selected by the user
def run_region(italy_map):
    print("-------------------------------------------------------------------------------------------")
    print()
    print("You chose to see the data divided by region.")
    print()
    print("Would you like to see the daily increase for a specific day or the latest update of the total?")
    user_date = input("Enter 'total' or a date in the format 'YYYYMMDD' between 20200224 and today: ")
    today = date.today().strftime("%Y%m%d")
    correct = check_date(user_date, today)
    while not correct:
        user_date = input("Please enter date again (YYYYMMDD): ")
        correct = check_date(user_date, today)
    print()
    print_region(italy_map, user_date)
    italy_map.show()


def print_region(italy_map, user_date):
    #based on the user's selection, the right file and the right column to read is selected.
    #the following part is similar to the one used for provinces:
    #data are printed out, and in the meantime the maximum value is found.
    if user_date == "total":
        raw_data_reg = requests.get(REG_DATA_URL).text.splitlines()
        column = "totale_casi"
    else:
        #the URL is build buy a fixed part stored in a variable, the date entered by the user and the file extension
        complete_url = REG_DATA_PREFIX + str(user_date) + ".csv"
        raw_data_reg = requests.get(complete_url).text.splitlines()
        column = "nuovi_positivi"
    max_value = find_max_reg(raw_data_reg, column)
    reader = csv.DictReader(raw_data_reg)
    for line in reader:
        latitude = float(line["lat"])
        longitude = float(line["long"])
        positives = float(line[column])
        print_dot(italy_map, latitude, longitude, positives, max_value)


def find_max_reg(raw_data_reg, column):
    #very similar to the function to find the maximum for provinces
    #due to the differences in how the datasets are built a second function was created
    #in a future version a merge of the two functions might be possible
    name_max_region = ""
    maximum_reg = national_total = 0
    reader = csv.DictReader(raw_data_reg)
    for line in reader:
        national_total += int(line[column])
        temp_value_reg = int(line[column])
        if temp_value_reg > maximum_reg:
            maximum_reg = temp_value_reg
            name_max_region = line["denominazione_regione"]
        print("In the region " + line["denominazione_regione"] + " there have been " + str(line[column]) + " cases.")
    print()
    print("-----------------------------------------------------------------")
    print("The highest no. of cases throughout all regions is found in " + name_max_region + ": " + str(maximum_reg) + " cases")
    print("The number of cases in the entire country is: " + str(national_total))
    return maximum_reg

###############################################
##               DATE CHECK                  ##
###############################################


def check_date(user_date, today):
    if user_date == "total":
        return True
    if not user_date.isdigit() or len(user_date) != 8:
        print("The value entered is not a number, it is too long or too short")
        return False
    year_t = int(today[:4])
    month_t = int(today[4:6])
    day_t = int(today[6:])
    year = int(user_date[:4])
    month = int(user_date[4:6])
    day = int(user_date[6:])
    if year < MIN_DATE[0] or year > year_t:
        print("Year is not within date range")
        return False
    if (year == MIN_DATE[0] and month < MIN_DATE[1]) or (year == year_t and month > month_t):
        print("Month is not within date range")
        return False
    if (month == MIN_DATE[1] and day < MIN_DATE[2]) or (month == month_t and day > day_t):
        print("Day is not within date range")
        return False
    if month in [1, 3, 5, 7, 8, 10, 12]:
        if day < 1 or day > 31:
            print("Day is not within month range (1-31)")
            return False
    if month in [4, 6, 9, 11]:
        if day < 1 or day > 30:
            print("Day is not within month range (1-30)")
            return False
    if year == 2020 and month == 2:
        if day < 1 or day > 29:
            print("Day is not within month range (1-29)")
            return False
    if year != 2020 and month == 2:
        if day < 1 or day > 28:
            print("Day is not within month range (1-28)")
            return False
    tz_rome = pytz.timezone('Europe/Rome')
    hour_rome = datetime.now(tz_rome).strftime("%H")
    if user_date == today and int(hour_rome) < 17:
        print("Today's data will be released after 5 pm CET.")
        return False
    return True

###############################################
##            PRINTING FUNCTION              ##
###############################################


def print_dot(italy_map, latitude, longitude, positives, max_value):
    #coordinates to place the dots come from the previous function
    coord_x = MAP_WIDTH * (longitude - MIN_LONGITUDE) / (MAX_LONGITUDE - MIN_LONGITUDE)
    coord_y = MAP_HEIGHT * (1 - (latitude - MIN_LATITUDE) / (MAX_LATITUDE - MIN_LATITUDE))
    #each dot is sized based on the highest value and multiplied by a factor 100
    dot_size = (positives / max_value) * 100
    circle = ImageDraw.Draw(italy_map)
    circle.ellipse((coord_x - dot_size / 2, coord_y - dot_size / 2, coord_x + dot_size / 2, coord_y + dot_size / 2), fill=(0, 123, 255))

###############################################
##               RERUN OPTION                ##
###############################################


def run_again():
    print()
    rerun = input("Would you like to run the program again? (y/n): ")
    while rerun != "y" and rerun != "n":
        print()
        rerun = input("You can only enter 'y' or 'n': ")
    if rerun == "n":
        print("Thanks for using this program! See you next time.")
    return rerun


if __name__ == "__main__":
    main()
