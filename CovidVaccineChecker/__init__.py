import os
import re
from sys import exit
import json
import time
import random
import requests
import tabulate
import datetime as dt
from inspect import stack
from hashlib import sha256
import PySimpleGUI as simpleGUI
# from CovidVaccineChecker.captcha import captcha_builder


def getCallingScriptFilename():
    # caller_frame = stack()
    # return caller_frame
    caller_frame = stack()[-1]
    return caller_frame[0].f_globals.get('__file__', None)


class TextColors:
    # print(f"\nCalling script: {os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))}")      # returns "(path)/__init__.py"

    __calling_script = getCallingScriptFilename()
    # print(f"Calling script: {__calling_script}")

    if 'schedule_vaccination_appointment.py' in __calling_script:
        HEADER = '\033[95m'
        SUCCESS = '\033[0;32m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        BLACKONGREY = '\033[1;30;47m'
        BLACKONYELLOW = '\033[1;30;43m'
        REDONBLACK = '\033[1;31;40m'
        ENDC = '\033[0m'
    else:
        # case when __calling_script is 'scheduler_form.py'
        HEADER = ''
        SUCCESS = ''
        WARNING = ''
        FAIL = ''
        BOLD = ''
        UNDERLINE = ''
        BLACKONGREY = ''
        BLACKONYELLOW = ''
        REDONBLACK = ''
        ENDC = ''


class CoWINAPI:
    BASE_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    secret = "U2FsdGVkX1/tQZSmh54vpi/QKFaw99sAGMzACIHBXfCijS/gI4DLzhzipWUdymVRpgb6tcgkZlFSK5Hm+cjkLQ=="
    headers = {
        'User-Agent': user_agent,
        'Origin': 'https://selfregistration.cowin.gov.in'
    }
    auth_headers = {
        'Authorization': None,
        'User-Agent': user_agent,
        'Origin': 'https://selfregistration.cowin.gov.in'
    }

    base_url = "https://cdn-api.co-vin.in/api/v2"

    generateOTP_url = base_url + "/auth/generateMobileOTP"
    confirmOTP_url = base_url + "/auth/validateMobileOtp"
    getStates_url = base_url + "/admin/location/states"
    getDistricts_url = base_url + "/admin/location/districts"                               # + "/{state_id}"
    getCalendarByDistrict_url = base_url + "/appointment/sessions/public/calendarByDistrict"
    findByPin_url = base_url + "/appointment/sessions/public/findByPin"
    findByDistrict_url = base_url + "/appointment/sessions/public/findByDistrict"
    beneficiaries_url = base_url + "/appointment/beneficiaries"
    schedule_url = base_url + "/appointment/schedule"
    captcha_url = base_url + "/auth/getRecaptcha"


    def __init__(self, mobile):
        self.mobile = mobile if mobile else ""
        self.token, self.state_id, self.state_name, self.district_id, self.district_name, self.pincode_preferences = None, None, None, None, None, None
        self.search_criteria, self.centre_preferences, self.slot_preference = None, list(), None
        self.appointment_date = (dt.datetime.today()).strftime("%d-%m-%Y")
        self.user_data = dict()

        self.appointment_slot_selected = None                       # value of slot selected at runtime
        self.appointment_centre_booked = None                       # name of centre booked for appointment


    @staticmethod
    def display_table(dict_list=None, user_config_data=None):
        """
        This function
            1. Takes a list of dictionary
            2. Add an Index column, and
            3. Displays the data in tabular format
        """
        if user_config_data is not None:
            # print(tabulate.tabulate(user_config_data, headers=['Variable', 'Value'], tablefmt="grid"))
            print(tabulate.tabulate(user_config_data, tablefmt="grid"))
            return

        header = ["idx"] + list(dict_list[0].keys())
        rows = [[idx + 1] + list(x.values()) for idx, x in enumerate(dict_list)]
        print(tabulate.tabulate(rows, header, tablefmt="grid"))


    def displayConfigFileData(self, user_config_file):
        with open(user_config_file, 'r') as json_file:
            user_data = json.load(json_file)

        # display_keys = ['mobile', 'state_id', 'district_id', 'pincode_preferences', 'search_criteria',
        #                 'centre_preferences', 'slot_preference', 'appointment_date']
        # for key in user_data.keys():
        #     if key in display_keys:
        #         if key in ['state_id', 'district_id']:
        #             print(f"{TextColors.SUCCESS}[+]{TextColors.ENDC} {TextColors.BOLD}{key.replace('_', ' ').title()}:{TextColors.ENDC} {user_data[key]}"
        #                   f"\t\t\t{TextColors.UNDERLINE}({user_data['state_name'] if key == 'state_id' else user_data['district_name']}){TextColors.ENDC}")
        #         elif key == 'search_criteria':
        #             print(f"{TextColors.SUCCESS}[+]{TextColors.ENDC} {TextColors.BOLD}{key.replace('_', ' ').title()}:{TextColors.ENDC} {user_data[key]}\t\t\t{TextColors.UNDERLINE}(1: by Pincode, 2: by District){TextColors.ENDC}")
        #         else:
        #             print(f"{TextColors.SUCCESS}[+]{TextColors.ENDC} {TextColors.BOLD}{key.replace('_', ' ').title()}:{TextColors.ENDC} {user_data[key]}")

        # display_keys = ['mobile', 'state_id', 'state_name', 'district_id', 'district_name', 'pincode_preferences', 'search_criteria',
        #                 'centre_preferences', 'slot_preference', 'appointment_date']
        # self.display_table(user_config_data=[[f"{TextColors.WARNING}{key.replace('_', ' ').title()}{TextColors.ENDC}", value]
        #                                      for key, value in user_data.items() if key in display_keys])

        display_keys = ['mobile', 'state_id', 'district_id', 'pincode_preferences', 'search_criteria',
                        'appointment_date', 'slot_preference', 'centre_preferences']
        key_value_list = list()
        for key, value in user_data.items():
            if key in display_keys:
                if key == 'state_id':
                    key_value_list.append([f"{TextColors.WARNING}{key.replace('_', ' ').title()}{TextColors.ENDC}", f"{value}   ({user_data['state_name']})"])
                elif key == 'district_id':
                    key_value_list.append([f"{TextColors.WARNING}{key.replace('_', ' ').title()}{TextColors.ENDC}", f"{value}  ({user_data['district_name']})"])
                elif key == 'search_criteria':
                    pincode = user_data['pincode_preferences'][0]
                    key_value_list.append([f"{TextColors.WARNING}{key.replace('_', ' ').title()}{TextColors.ENDC}",
                                           f"Search by {f'Pincode ({pincode})' if user_data['search_criteria'] == 1 else 'District'}"])
                elif key == 'slot_preference':
                    key_value_list.append([f"{TextColors.WARNING}{key.replace('_', ' ').title()}{TextColors.ENDC}", "Select random slot" if user_data['slot_preference'] == 1 else "Enter manually when a valid centre is found"])
                else:
                    key_value_list.append([f"{TextColors.WARNING}{key.replace('_', ' ').title()}{TextColors.ENDC}", value])

        self.display_table(user_config_data=key_value_list)


    def save_user_config(self, user_config_file):
        try:
            if os.path.exists(user_config_file):
                os.remove(user_config_file)
            self.user_data = {
                "mobile": self.mobile,
                "token": self.token,
                "state_id": self.state_id,
                "state_name": self.state_name,
                "district_id": self.district_id,
                "district_name": self.district_name,
                "pincode_preferences": self.pincode_preferences,
                "search_criteria": self.search_criteria,
                "appointment_date": self.appointment_date,
                "slot_preference": self.slot_preference,
                "centre_preferences": self.centre_preferences
            }

            with open(user_config_file, 'w') as json_file:
                json_file.write(json.dumps(self.user_data, indent=4))
        except Exception as e:
            if os.path.exists(user_config_file):
                os.remove(user_config_file)
            print(f"\n{TextColors.FAIL}File could not be saved (message: {e}). Please try again...{TextColors.ENDC}")
            exit(1)


    def update_user_config(self, list_of_keys_to_update, value_list, user_config_file):
        print("\n-->\tUpdating user config file... ", end="")
        for idx, key in enumerate(list_of_keys_to_update):
            self.user_data[key] = value_list[idx]

        with open(user_config_file, 'w') as json_file:
            json_file.write(json.dumps(self.user_data, indent=4))

        print("DONE")


    def get_user_data(self):
        return self.user_data


    def use_existing_user_config(self, user_config_file):
        with open(user_config_file, 'r') as json_file:
            self.user_data = json.load(json_file)

        self.token = self.user_data['token']
        self.state_id = self.user_data['state_id']
        self.state_name = self.user_data['state_name']
        self.district_id = self.user_data['district_id']
        self.district_name = self.user_data['district_name']
        self.pincode_preferences = self.user_data['pincode_preferences']
        self.search_criteria = self.user_data['search_criteria']
        self.appointment_date = self.user_data['appointment_date']
        self.slot_preference = self.user_data['slot_preference']
        self.centre_preferences = self.user_data['centre_preferences']

        self.auth_headers['Authorization'] = f'Bearer {self.token}'


    def create_new_user_config(self, user_config_file):
        print(f"\n-->\tUsing mobile number: {self.mobile}")

        if os.path.exists(user_config_file):
            self.use_existing_user_config(user_config_file)
            # self.generateUserToken(user_config_file, save_token_in_file=True, refresh_token=False)
        else:
            self.generateUserToken(user_config_file, save_token_in_file=False, refresh_token=False)

        print("\n-->\tGetting state, district and pincode preferences")

        while True:
            try:
                self.state_id, self.state_name, self.district_id, self.district_name, self.pincode_preferences = self.getStateDistrictPincodePreferences()
                break
            except Exception:
                if os.path.exists(user_config_file):
                    self.generateUserToken(user_config_file, save_token_in_file=True, refresh_token=True)
                else:
                    self.generateUserToken(user_config_file, save_token_in_file=False, refresh_token=True)

        while True:
            self.search_criteria = input(f"\n-->\tEnter search criteria {TextColors.WARNING}('1' to search by pincode, '2' to search by district){TextColors.ENDC}\n"
                                         f"{TextColors.BOLD}Note: in case of search by pincode, first pincode will be selected "
                                         f"from your pincode preferences:{TextColors.ENDC} ")

            if self.search_criteria is not None or self.search_criteria.strip() != "":
                self.search_criteria = int(self.search_criteria.strip())
                if self.search_criteria in [1, 2]:
                    break
                else:
                    print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

        date = input("\n-->\tEnter appointment date to check available slots for that date "
                     f"{TextColors.WARNING}(Format: dd-mm-yyyy, can be today's date or of the future, "
                     f"defaults to today if nothing or incorrect date format is entered){TextColors.ENDC}: ")

        if date.strip() != "":
            try:
                self.appointment_date = dt.datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')

                if not self.is_appointment_date_valid():
                    self.appointment_date = (dt.datetime.today()).strftime('%d-%m-%Y')
                    print(f"\n{TextColors.FAIL}Incorrect date entered. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")
            except ValueError:
                self.appointment_date = (dt.datetime.today()).strftime('%d-%m-%Y')
                print(f"\n{TextColors.FAIL}Incorrect date format, should have been dd-mm-yyyy. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")
        else:
            self.appointment_date = (dt.datetime.today()).strftime('%d-%m-%Y')
            print(f"\n{TextColors.FAIL}No date entered. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")

        while True:
            self.slot_preference = input(f"\n-->\tEnter slot preference ID {TextColors.WARNING}(SELECT ONE) ['1' to 'Select random slot', '2' to 'Enter manually when a valid centre is found']{TextColors.ENDC}: ")

            if self.slot_preference is not None or self.slot_preference.strip() != "":
                try:
                    self.slot_preference = int(self.slot_preference.strip())
                    if 0 < self.slot_preference < 3:
                        break
                    else:
                        print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned options{TextColors.ENDC}")
                except Exception:
                    print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned options{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned options{TextColors.ENDC}")

        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} {TextColors.UNDERLINE}{TextColors.BOLD}TIP FOR NEXT INPUT:{TextColors.ENDC} "
              f"{TextColors.BOLD}If you prefer centre with name 'Swami Ram Hospital (Garhi Cantt.)' & 'Centre Name 2' type "
              f"either a part of their name or full name in the original order, for example, 'ram hospital, centre name' "
              f"or 'swami ram, centre name 2', etc.{TextColors.ENDC}")
        input("\nPress 'Enter' to get a list of all available centres in your district and then input your centre preference...")
        self.getCalendarByDistrict(user_config_file)
        # print(f"\n{TextColors.BOLD}Note: The above mentioned values for 'Min Age, Available Capacity and Slots' are for one of the sessions "
        #       f"at that centre only. You can still enter a centre's name below as your preference as there might be other sessions as well in "
        #       f"the same centre with different 'Min Age, Available Capacity and Slots' value.{TextColors.ENDC}")
        centre_preferences = input(f"\n-->\tEnter short/full centre name for centre preference "
                                   f"{TextColors.WARNING}(comma-separated in case of multiple), CAN BE BLANK AS WELL{TextColors.ENDC}: ")

        if centre_preferences is not None and centre_preferences.strip() != "":
            self.centre_preferences = centre_preferences.strip().replace(', ', ',').replace(' ,', ',').lower().split(",")
            self.centre_preferences = [centre for centre in self.centre_preferences if centre != '']
        else:
            self.centre_preferences = []

        print(f"\n-->\tSaving user configuration to file '{user_config_file}'... ")

        self.save_user_config(user_config_file)


    def is_appointment_date_valid(self):
        today = dt.datetime.today().strftime('%d-%m-%Y')

        return bool(dt.datetime.strptime(self.appointment_date, '%d-%m-%Y') >= dt.datetime.strptime(today, '%d-%m-%Y'))


    def changeAppointmentDate(self, user_config_file, load_values_from_existing_config_first = True):
        if load_values_from_existing_config_first:
            self.use_existing_user_config(user_config_file)        # to initialise all other variables too, before calling update_user_config()

        date = input("\n-->\tEnter appointment date to check available slots for that date "
                     f"{TextColors.WARNING}(Format: dd-mm-yyyy, can be today's date or of the future, "
                     f"defaults to today if nothing or incorrect date format is entered){TextColors.ENDC}: ")

        if date.strip() != "":
            try:
                self.appointment_date = dt.datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')

                if not self.is_appointment_date_valid():
                    self.appointment_date = (dt.datetime.today()).strftime('%d-%m-%Y')
                    print(f"\n{TextColors.FAIL}Incorrect date entered. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")
            except ValueError:
                self.appointment_date = (dt.datetime.today()).strftime('%d-%m-%Y')
                print(f"\n{TextColors.FAIL}Incorrect date format, should have been dd-mm-yyyy. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")
        else:
            self.appointment_date = (dt.datetime.today()).strftime('%d-%m-%Y')
            print(f"\n{TextColors.FAIL}No date entered. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")

        self.update_user_config(['appointment_date'], [self.appointment_date], user_config_file)


    def changeSearchCriteria(self, user_config_file, load_values_from_existing_config_first = True):
        if load_values_from_existing_config_first:
            self.use_existing_user_config(user_config_file)        # to initialise all other variables too, before calling update_user_config()

        while True:
            self.search_criteria = input(f"\n-->\tEnter search criteria {TextColors.WARNING}('1' to search by pincode, '2' to search by district){TextColors.ENDC}\n"
                                         f"{TextColors.BOLD}Note: in case of search by pincode, first pincode will be selected "
                                         f"from your pincode preferences:{TextColors.ENDC} ")

            if self.search_criteria is not None or self.search_criteria.strip() != "":
                self.search_criteria = int(self.search_criteria.strip())
                if self.search_criteria in [1, 2]:
                    break
                else:
                    print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

        self.update_user_config(['search_criteria'], [self.search_criteria], user_config_file)


    def changeSlotPreference(self, user_config_file, load_values_from_existing_config_first = True):
        if load_values_from_existing_config_first:
            self.use_existing_user_config(user_config_file)        # to initialise all other variables too, before calling update_user_config()

        while True:
            self.slot_preference = input(f"\n-->\tEnter slot preference ID {TextColors.WARNING}(SELECT ONE) ['1' to 'Select random slot', '2' to 'Enter manually when a valid centre is found']{TextColors.ENDC}: ")

            if self.slot_preference is not None or self.slot_preference.strip() != "":
                try:
                    self.slot_preference = int(self.slot_preference.strip())
                    if 0 < self.slot_preference < 3:
                        break
                    else:
                        print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned options{TextColors.ENDC}")
                except Exception:
                    print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned options{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned options{TextColors.ENDC}")

        self.update_user_config(['slot_preference'], [self.slot_preference], user_config_file)


    def getUserSlotPreference(self, centre):
        available_slots = centre['slots']

        slots_string = "\n".join([f'{idx+1}. {slot}' for idx, slot in enumerate(available_slots)])

        print(f"\n{TextColors.WARNING}Available slots at '{centre['name']}':\n{slots_string}{TextColors.ENDC}")

        if self.slot_preference == 1:
            random_index = random.randint(0, len(available_slots) - 1)
            slot_selected = available_slots[random_index]
            print(f"\n{TextColors.BLACKONGREY}RANDOM SLOT SELECTED: {slot_selected}{TextColors.ENDC}")
        else:
            while True:
                slot_selected = input(f"\nEnter preferred slot ID {TextColors.WARNING}(SELECT ONE){TextColors.ENDC}: ")

                if slot_selected is not None or slot_selected.strip() != "":
                    try:
                        slot_selected = int(slot_selected.strip())
                        if 0 < slot_selected <= len(available_slots):
                            slot_selected = available_slots[slot_selected - 1]
                            break
                        else:
                            print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned slots{TextColors.ENDC}")
                    except Exception:
                        print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned slots{TextColors.ENDC}")
                else:
                    print(f"\n{TextColors.FAIL}Invalid input! Please select one of the above mentioned slots{TextColors.ENDC}")

        return slot_selected


    def generateUserToken(self, user_config_file, save_token_in_file=True, refresh_token=False):
        if refresh_token:
            print(f"\n{TextColors.FAIL}Previous TOKEN Expired!!!{TextColors.ENDC}")

        print(f"\n-->\tGenerating OTP {TextColors.WARNING}(There might be some delay in receiving the OTP, please wait atleast 2 minutes){TextColors.ENDC}")
        txnId = ""

        while True:
            txnId_new = self.generateOTP()

            if txnId_new == txnId:
                print(f"{TextColors.WARNING}[+]{TextColors.ENDC} Last generated OTP still valid! New OTP will be generated only after expiration time of 3 mins.")

            txnId = txnId_new

            otp = input("\n-->\tEnter OTP received on your mobile phone (Press 'Enter' to resend OTP): ")

            if otp is None or otp.strip() == "":
                continue

            otp = otp.strip()

            # print("\n-->\tHashing OTP to SHA256, to authenticate it in next step")

            hashed_otp = sha256(otp.encode("utf-8")).hexdigest()

            # print(f"\nhashed OTP: {hashed_otp}")

            print("\n-->\tValidating 'OTP' to get token")

            self.token = self.confirmOTP(hashed_otp, txnId)

            if self.token is not None:
                break

        self.auth_headers['Authorization'] = f'Bearer {self.token}'

        if save_token_in_file:
            self.update_user_config(['token'], [self.token], user_config_file)


    def generateOTP(self):
        payload = json.dumps({
            "mobile": self.mobile,
            "secret": self.secret
        })

        while True:
            response = requests.request("POST", self.generateOTP_url, headers=self.headers, data=payload)

            try:
                txnId = response.json()['txnId']
                print(f"\ntxnId: {txnId}\t(SUCCESS)")
                break
            except Exception as e:
                print(f"{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})... trying again in 3 seconds")
                pass

            time.sleep(3)

        return txnId


    def confirmOTP(self, hashed_otp, txnId):
        payload = json.dumps({
            "otp": hashed_otp,
            "txnId": txnId
        })

        response = requests.request("POST", self.confirmOTP_url, headers=self.headers, data=payload)

        try:
            token = response.json()["token"]
            print(f"\n{TextColors.BOLD}TOKEN OBTAINED:{TextColors.ENDC} {token}")
            return token
        except Exception as e:
            if "invalid otp" in response.text.lower() or "unauthenticated access" in response.text.lower():
                print(f"\n{TextColors.FAIL}INCORRECT OTP ENTERED!!! Please enter the correct OTP{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
            return None


    def getStateDistrictPincodePreferences(self):
        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Getting list of all states\n")
        response = requests.request("GET", self.getStates_url, headers=self.auth_headers)

        if response.status_code == 200:
            try:
                self.display_table(response.json()['states'])

                while True:
                    state_id = input("\nEnter state ID: ")
                    ids_list = [str(state['state_id']) for state in response.json()['states']]
                    if state_id.strip() not in ids_list:
                        print(f"\n{TextColors.FAIL}Invalid input! Please enter correct state ID{TextColors.ENDC}")
                        continue
                    state_id = int(state_id.strip())
                    state_name = [state['state_name'] for state in response.json()['states'] if state['state_id'] == state_id][0]
                    break

                print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Getting list of all districis in '{state_name}'\n")
                response = requests.request("GET", self.getDistricts_url + "/" + str(state_id), headers=self.auth_headers)

                if response.status_code == 200:
                    self.display_table(response.json()['districts'])

                    while True:
                        district_id = input("\nEnter district ID: ")
                        ids_list = [str(district['district_id']) for district in response.json()['districts']]
                        if district_id.strip() not in ids_list:
                            print(f"\n{TextColors.FAIL}Invalid input! Please enter correct district ID{TextColors.ENDC}")
                            continue
                        district_id = int(district_id.strip())
                        district_name = [district['district_name'] for district in response.json()['districts'] if district['district_id'] == district_id][0]
                        break
                else:
                    print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: Error getting districts list){TextColors.ENDC} (response: {response.text})")
                    exit(1)
            except Exception as e:
                print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC}")
                exit(1)
        else:
            raise Exception(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: Error getting states list){TextColors.ENDC} (response: {response.text})")

        pincode_pattern = re.compile("^[1-9][0-9]{5}$")
        while True:
            pincode_preferences = input(f"\nEnter pincode preference(s) {TextColors.WARNING}(comma-separated in case of multiple){TextColors.ENDC}: ")

            if pincode_preferences is not None and pincode_preferences.strip() != "":
                pincode_list = pincode_preferences.strip().replace(" ", "").split(",")
                areValidPincodes = [bool(pincode_pattern.match(pincode)) for pincode in pincode_list if pincode != '']
                if False not in areValidPincodes:
                    pincode_preferences = [int(pincode) for pincode in pincode_list if pincode != '']
                    break
                else:
                    print(f"\n{TextColors.FAIL}Invalid input! Please enter correct pincode (rule: 6-digit number not starting with zero and no spaces in between){TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please enter correct pincode (rule: 6-digit number not starting with zero and no spaces in between){TextColors.ENDC}")

        return state_id, state_name, district_id, district_name, pincode_preferences


    def getCalendarByDistrict(self, user_config_file):
        # Returns empty list as response.json()['centers']=[] if there are now no ongoing sessions in all the centres
        params = {
            "district_id": self.district_id,
            "date": self.appointment_date,
            # "min_age_limit": 18,
            # "vaccine": "COVISHIELD"
        }

        while True:
            print(f"\n-->\tGetting list of centres for district '{self.district_name}', using date '{self.appointment_date}'\n")
            response = requests.request("GET", self.getCalendarByDistrict_url, headers=self.auth_headers, params=params)

            try:
                all_centres = response.json()['centers']
                # print(json.dumps(all_centres, indent=4))
                if len(all_centres) == 0:
                    print(f"{TextColors.FAIL}No Centre Found{TextColors.ENDC} (Seems like there are now no ongoing vaccination "
                          f"sessions for this date. Try changing the date to get a list of all available centres)")

                    while True:
                        answer = input(f"\n-->\tEnter choice {TextColors.WARNING}(Change appointment date (c) / Quit (q)){TextColors.ENDC}: ")

                        if answer.lower().strip() == 'c':
                            self.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
                            break
                        elif answer.lower().strip() == 'q':
                            print("\nExiting program...")
                            exit(1)
                        else:
                            print(f"\n{TextColors.FAIL}Invalid input!{TextColors.ENDC}")
                else:
                    centres_list = [
                        {"Centre Name": centre['name'], "District": centre['district_name'], "Pincode": centre['pincode'],
                         "Vaccine Available": "\n".join(sorted(set([session['vaccine'] for session in centre['sessions']]))),
                         "Fee Type": centre['fee_type'],
                         "Accepted Age Groups": ", ".join(sorted(list(map(lambda x: str(x)+'+', set([session['min_age_limit'] for session in centre['sessions']]))))),
                         # "Available Capacity": f"Dose 1: {centre['sessions'][0]['available_capacity_dose1']}\nDose 2: {centre['sessions'][0]['available_capacity_dose2']}",
                         # "Slots": "\n".join(centre['sessions'][0]['slots'])
                         } for centre in all_centres]

                    self.display_table(centres_list)

                    print(f"\n{TextColors.BLACKONGREY}Total Centres Found: {len(all_centres)}{TextColors.ENDC}")
                    break
            except Exception as e:
                print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
                while True:
                    answer = input(f"\n-->\tEnter choice {TextColors.WARNING}(Change appointment date (c) / Quit (q)){TextColors.ENDC}: ")

                    if answer.lower().strip() == 'c':
                        self.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
                        break
                    elif answer.lower().strip() == 'q':
                        print("\nExiting program...")
                        exit(1)
                    else:
                        print(f"\n{TextColors.FAIL}Invalid input!{TextColors.ENDC}")


    def findCentresByPin(self):
        # Returns empty list as response.json()['sessions']=[] if there are institutes present but are all booked or none of them have opened booking slots yet
        params = {
            "pincode": self.pincode_preferences[0],
            "date": self.appointment_date,
        }

        response = requests.request("GET", self.findByPin_url, headers=self.auth_headers, params=params)

        try:
            all_centres = response.json()['sessions']
        except Exception as e:
            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
            exit(1)

        return all_centres


    def findCentresByDistrict(self):
        # Returns empty list as response.json()['sessions']=[] if there are institutes present but are all booked or none of them have opened booking slots yet
        params = {
            "district_id": self.district_id,
            "date": self.appointment_date,
            # "min_age_limit": 18,
            # "vaccine": "COVISHIELD"
        }

        response = requests.request("GET", self.findByDistrict_url, headers=self.auth_headers, params=params)

        try:
            all_centres = response.json()['sessions']
        except Exception as e:
            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
            exit(1)

        return all_centres


    def findCentresBySearchCriteria(self):
        # Returns empty list as response.json()['sessions']=[] if there are institutes present but are all booked or none of them have opened booking slots yet
        if self.search_criteria == 1:
            print(f"\n-->\tGetting list of centres for pincode '{self.pincode_preferences[0]}' (first pincode in your preferences), using date '{self.appointment_date}'\n")

            all_centres = self.findCentresByPin()
        else:
            print(f"\n-->\tGetting list of centres for district '{self.district_name}', using date '{self.appointment_date}'\n")

            all_centres = self.findCentresByDistrict()

        return all_centres


    def get_beneficiaries(self):
        response = requests.request("GET", self.beneficiaries_url, headers=self.auth_headers)

        try:
            beneficiaries = response.json()['beneficiaries']
        except Exception as e:
            if "unauthenticated access" not in response.text.lower():
                print(f"{TextColors.FAIL}{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC}{TextColors.ENDC} (response: {response.text})\n")
            beneficiaries = None

        return beneficiaries, response.status_code


    @staticmethod
    def get_vaccination_status_details(vaccination_status, dose1_date, dose2_date):
        if vaccination_status.lower() == "not vaccinated":
            vaccination_status_details = vaccination_status
        elif vaccination_status.lower() == "partially vaccinated":
            vaccination_status_details = f"{vaccination_status}\n(Dose 1: {dose1_date})\n(Dose 2:     -     )"
        else:
            vaccination_status_details = f"{vaccination_status}\n(Dose 1: {dose1_date})\n(Dose 2: {dose2_date})"

        return vaccination_status_details


    @staticmethod
    def get_appointment_details(appointment_dict):
        appointment_details = f"{TextColors.HEADER}Apt. ID:{TextColors.ENDC} {appointment_dict['appointment_id']}\n" \
                              f"{TextColors.HEADER}Centre:{TextColors.ENDC} {appointment_dict['name']}\n" \
                              f"{TextColors.HEADER}Date:{TextColors.ENDC} {appointment_dict['date']}\n" \
                              f"{TextColors.HEADER}Slot:{TextColors.ENDC} {appointment_dict['slot']}"

        return appointment_details


    # def generate_captcha(self, user_config_file, is_app_gui):
    #     print(f"\n{TextColors.HEADER}============================= GENERATING CAPTCHA ============================={TextColors.ENDC}")
    #
    #     while True:
    #         response = requests.request("POST", self.captcha_url, headers=self.auth_headers)
    #
    #         if response.status_code == 200:
    #             print(f"\nCAPTCHA GENERATED!!!")
    #             # with open("response_captcha.json", "w") as captcha_json_file:
    #             #     captcha_json_file.write(json.dumps(response.json(), indent=4))
    #             return captcha_builder(response.json())
    #         else:
    #             if "unauthenticated access" in response.text.lower():
    #                 if is_app_gui:
    #                     return '<REFRESH_TOKEN>'
    #                 self.generateUserToken(user_config_file, refresh_token=True)
    #             else:
    #                 print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: could not generate captcha){TextColors.ENDC} (response: {response.text})... trying again in 1 sec.")
    #                 time.sleep(1)


    def isValidCentre(self, centre, min_age_limit, vaccine_preference):
        isValidPincode, isValidInstitute, isValidMinAgeSelected, isValidVaccine = False, False, False, True

        if self.search_criteria == 1:
            isValidPincode = True if centre['pincode'] == self.pincode_preferences[0] else False
        elif self.search_criteria == 2:
            isValidPincode = True if centre['pincode'] in self.pincode_preferences else False

        if len(self.centre_preferences) > 0:
            for institue in self.centre_preferences:
                isValidInstitute = True if institue in centre['name'].lower() else False
                if isValidInstitute:
                    break
        else:
            isValidInstitute = True             # because in case of no preference, institute name doesn't matter

        isValidMinAgeSelected = True if centre['min_age_limit'] == min_age_limit else False

        if vaccine_preference:
            isValidVaccine = True if centre['vaccine'].lower() == vaccine_preference else False

        isValidCentre = isValidPincode and isValidInstitute and isValidMinAgeSelected and isValidVaccine

        # print(f"centre vaccine: {centre['vaccine']}, is vaccine valid? {isValidVaccine}, is centre valid? {isValidCentre}")
        return isValidCentre


    def schedule_appointment(self, all_centres, ref_ids, dose_number, min_age_limit, vaccine_preference, user_config_file, is_app_gui=False):
        appointment_booked_flag = False
        appointment_id = None

        if len(all_centres) == 0:
            print(f"\n{TextColors.FAIL}No vaccination centre found!{TextColors.ENDC}", end="")
            return appointment_booked_flag, appointment_id

        print(f"\nRef. IDs to schedule booking for: {ref_ids}")

        total_centres = len(all_centres)

        for idx, centre in enumerate(all_centres):
            print(f"\n[+] trying centre ({idx+1}/{total_centres}) '{centre['name']}'\n\t{TextColors.BOLD}{TextColors.WARNING}(Vaccine Available: {centre['vaccine']}, Accepted Age Group: {centre['min_age_limit']}+){TextColors.ENDC}...", end=" ")

            dummy_centre_check = False
            # dummy_centre_check = 'aiims' in centre['name'].lower()

            if self.isValidCentre(centre, min_age_limit, vaccine_preference) or dummy_centre_check:
                print(f"{TextColors.BOLD}{TextColors.WARNING}(VALID CENTRE FOUND - Booking Appointment...){TextColors.ENDC}")
                if centre['available_capacity_dose'+str(dose_number)] >= len(ref_ids):
                    # captcha = self.generate_captcha(user_config_file, is_app_gui)
                    #
                    # if captcha == '<REFRESH_TOKEN>' and is_app_gui:
                    #     return False, '<REFRESH_TOKEN>'
                    #
                    # print(f"\n{TextColors.BLACKONGREY}Entered Captcha Value: {captcha}{TextColors.ENDC}")

                    payload = json.dumps({
                        "dose": dose_number,
                        "center_id": centre['center_id'],
                        "session_id": centre['session_id'],
                        # "slot": self.slot_preference,
                        "slot": self.getUserSlotPreference(centre) if not is_app_gui else self.getUserSlotPreferencePopup(centre),
                        "beneficiaries": ref_ids,
                        # "captcha": captcha
                    })

                    response = requests.request("POST", self.schedule_url, headers=self.auth_headers, data=payload)

                    try:
                        appointment_id = response.json()['appointment_confirmation_no']
                        print(f"\n{TextColors.SUCCESS}[+]{TextColors.ENDC} SUCCESS: '{centre['name']}, {centre['address']}' centre successfully booked for {self.appointment_date} for selected beneficiaries")
                        print(f"\n{TextColors.BLACKONGREY}Appointment Confirmation Number: {appointment_id}{TextColors.ENDC}")
                        appointment_booked_flag = True
                        self.appointment_centre_booked = centre['name']
                        break
                    except Exception as e:
                        if "unauthenticated access" in response.text.lower():
                            if is_app_gui:
                                return False, '<REFRESH_TOKEN>'
                            self.generateUserToken(user_config_file, refresh_token=True)
                        else:
                            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
                else:
                    print(f"\n{TextColors.FAIL}FAILED: Vaccine shots available in this centre are less than the number of beneficiaries selected{TextColors.ENDC}")

        return appointment_booked_flag, appointment_id


    """
    -------------------------------------------------------------------------------------------------------------------------------
    ------------------------------------------- New Methods TO SUPPORT GUI WINDOW CALLS -------------------------------------------
    -------------------------------------------------------------------------------------------------------------------------------
    """


    def update_class_variable(self, key, value, update_user_config=False, user_config_file=None):
        if key != 'token':
            print(f"\n-->\tUpdating class variable '{key}' with value '{value}'... ")
        else:
            print(f"\n-->\tUpdating class variable '{key}'... ")

        if key == 'mobile':
            self.mobile = value
        elif key == 'token':
            self.token = value
            self.auth_headers['Authorization'] = f'Bearer {self.token}'
        elif key == 'state_id':
            self.state_id = value
        elif key == 'state_name':
            self.state_name = value
        elif key == 'district_id':
            self.district_id = value
        elif key == 'district_name':
            self.district_name = value
        elif key == 'pincode_preferences':
            self.pincode_preferences = value
        elif key == 'search_criteria':
            self.search_criteria = value
        elif key == 'centre_preferences':
            self.centre_preferences = value
        elif key == 'slot_preference':
            self.slot_preference = value
        elif key == 'appointment_date':
            self.appointment_date = value

        if update_user_config:
            self.update_user_config([key], [value], user_config_file)


    def get_stateDict(self):
        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Getting list of all states")
        response = requests.request("GET", self.getStates_url, headers=self.auth_headers)

        if response.status_code == 200:
            # print(response.text)
            states = response.json()['states']
            state_dict = dict()

            for state in states:
                state_dict[state['state_name']] = state['state_id']

            return state_dict
        else:
            raise Exception(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: Error getting states list){TextColors.ENDC} (response: {response.text}")


    def get_districtDict(self, state_id):
        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Getting list of all districts")
        response = requests.request("GET", self.getDistricts_url + "/" + str(state_id), headers=self.auth_headers)

        if response.status_code == 200:
            districts = response.json()['districts']
            district_dict = dict()

            for district in districts:
                district_dict[district['district_name']] = district['district_id']

            return district_dict
        else:
            raise Exception(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: Error getting districts list){TextColors.ENDC} (response: {response.text}")


    @staticmethod
    def get_lists_from_list(data_list, num_elements_in_sublist):
        return [data_list[i:i+num_elements_in_sublist] for i in range(0, len(data_list), num_elements_in_sublist)]


    def getUserSlotPreferencePopup(self, centre):
        available_slots = centre['slots']

        slots_string = "\n".join([f'{idx+1}. {slot}' for idx, slot in enumerate(available_slots)])

        print(f"\n{TextColors.WARNING}Available slots at '{centre['name']}':\n{slots_string}{TextColors.ENDC}")

        if self.slot_preference == 1:
            random_index = random.randint(0, len(available_slots) - 1)
            self.appointment_slot_selected = available_slots[random_index]
            print(f"\n{TextColors.BLACKONGREY}RANDOM SLOT SELECTED: {self.appointment_slot_selected}{TextColors.ENDC}")
        else:
            radio_buttons_list = [simpleGUI.Radio(f'{slot}', key=f'radio{idx+1}', group_id=1) for idx, slot in enumerate(available_slots)]

            window = simpleGUI.Window('Choose Slot', finalize=True).Layout([[simpleGUI.Text('Choose a slot from the following options to proceed')],
                                                                            self.get_lists_from_list(radio_buttons_list, 1),
                                                                            [simpleGUI.Submit()]])
            window.finalize()
            window['radio1'].update(value=True)

            event, values = window.read()
            # print(f"Event: {event}\nValues: {json.dumps(values, indent=4)}\n")

            if event == simpleGUI.WIN_CLOSED:
                simpleGUI.popup("Slot has not been selected! Invalid input detected from the user\n\nProgram will now exit...",
                                title="Slot Selection Error")
                exit(1)

            for i in range(1, len(available_slots) + 1):
                if values[f'radio{i}']:
                    self.appointment_slot_selected = window[f'radio{i}'].Text

            window.close()
            print(f"\n{TextColors.BLACKONGREY}SLOT SELECTED: {self.appointment_slot_selected}{TextColors.ENDC}")

        return self.appointment_slot_selected
