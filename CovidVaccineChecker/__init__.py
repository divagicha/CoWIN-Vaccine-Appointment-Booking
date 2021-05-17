import os
# import sys
import json
import time
import requests
import tabulate
import datetime as dt
from hashlib import sha256
from CovidVaccineChecker.captcha import captcha_builder


class TextColors:
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


class CoWINAPI:
    BASE_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    secret = "U2FsdGVkX1+LQcQNX+RTIipW+jdFWg02BOScu2dJksHYVYzKd3h2oAbeECbhE4SrYB0JIkVLHf4cSdxK7uSmiA=="
    headers = {
        'User-Agent': user_agent
    }
    auth_headers = {
        'Authorization': None,
        'User-Agent': user_agent
    }

    base_url = "https://cdn-api.co-vin.in/api/v2"

    generateOTP_url = base_url + "/auth/generateMobileOTP"
    confirmOTP_url = base_url + "/auth/validateMobileOtp"
    getStates_url = base_url + "/admin/location/states"
    getDistricts_url = base_url + "/admin/location/districts"                               # + "/{state_id}"
    findByPin_url = base_url + "/appointment/sessions/public/findByPin"
    findByDistrict_url = base_url + "/appointment/sessions/public/findByDistrict"
    beneficiaries_url = base_url + "/appointment/beneficiaries"
    schedule_url = base_url + "/appointment/schedule"
    captcha_url = base_url + "/auth/getRecaptcha"


    def __init__(self, mobile):
        self.mobile = mobile
        self.token, self.state_id, self.state_name, self.district_id, self.district_name, self.pincode_preferences = None, None, None, None, None, None
        self.search_criteria, self.institution_preferences, self.slot_preference = None, list(), None
        self.appointment_date = (dt.datetime.today()).strftime("%d-%m-%Y")
        self.user_data = dict()


    @staticmethod
    def display_table(dict_list):
        """
        This function
            1. Takes a list of dictionary
            2. Add an Index column, and
            3. Displays the data in tabular format
        """
        header = ["idx"] + list(dict_list[0].keys())
        rows = [[idx + 1] + list(x.values()) for idx, x in enumerate(dict_list)]
        print(tabulate.tabulate(rows, header, tablefmt="grid"))


    @staticmethod
    def displayConfigFileData(user_config_file):
        with open(user_config_file, 'r') as json_file:
            user_data = json.load(json_file)

            display_keys = ['mobile', 'state_id', 'district_id', 'pincode_preferences', 'search_criteria',
                            'institution_preferences', 'slot_preference', 'appointment_date']
            for key in user_data.keys():
                if key in display_keys:
                    if key in ['state_id', 'district_id']:
                        print(f"{TextColors.SUCCESS}[+]{TextColors.ENDC} {TextColors.BOLD}{key.replace('_', ' ').title()}:{TextColors.ENDC} {user_data[key]}"
                              f"\t\t\t{TextColors.UNDERLINE}({user_data['state_name'] if key == 'state_id' else user_data['district_name']}){TextColors.ENDC}")
                    elif key == 'search_criteria':
                        print(f"{TextColors.SUCCESS}[+]{TextColors.ENDC} {TextColors.BOLD}{key.replace('_', ' ').title()}:{TextColors.ENDC} {user_data[key]}\t\t\t{TextColors.UNDERLINE}(1: by Pincode, 2: by District){TextColors.ENDC}")
                    else:
                        print(f"{TextColors.SUCCESS}[+]{TextColors.ENDC} {TextColors.BOLD}{key.replace('_', ' ').title()}:{TextColors.ENDC} {user_data[key]}")


    def save_user_config(self, user_config_file):
        self.user_data = {
            "mobile": self.mobile,
            "token": self.token,
            "state_id": self.state_id,
            "state_name": self.state_name,
            "district_id": self.district_id,
            "district_name": self.district_name,
            "pincode_preferences": self.pincode_preferences,
            "search_criteria": self.search_criteria,
            "institution_preferences": self.institution_preferences,
            "slot_preference": self.slot_preference,
            "appointment_date": self.appointment_date
        }

        with open(user_config_file, 'x') as json_file:
            json_file.write(json.dumps(self.user_data, indent=4))


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
        self.institution_preferences = self.user_data['institution_preferences']
        self.slot_preference = self.user_data['slot_preference']
        self.appointment_date = self.user_data['appointment_date']

        self.auth_headers['Authorization'] = f'Bearer {self.token}'


    def create_new_user_config(self, user_config_file):
        print(f"\n-->\tUsing mobile number: {self.mobile}")

        while True:
            print(f"\n-->\tGenerating OTP {TextColors.WARNING}(There might be some delay in receiving the OTP, please wait atleast 2 minutes){TextColors.ENDC}\n")

            txnId = self.generateOTP()

            otp = input("\nEnter OTP received on your mobile phone (Press 'Enter' to resend OTP): ")

            if otp is not None and otp.strip() != "":
                break

        print("\n-->\tHashing OTP to SHA256, to authenticate it in next step")

        hashed_otp = sha256(otp.encode("utf-8")).hexdigest()

        print(f"\nhashed OTP: {hashed_otp}")

        print("\n-->\tValidating 'OTP' and 'txnId' to get token")

        self.token = self.confirmOTP(hashed_otp, txnId)

        self.auth_headers['Authorization'] = f'Bearer {self.token}'

        print("\n-->\tGetting state, district and pincode preferences")

        while True:
            try:
                self.state_id, self.state_name, self.district_id, self.district_name, self.pincode_preferences = self.getStateDistrictPincodePreferences()
                break
            except Exception:
                self.refreshToken(user_config_file, save_token_in_file=False)

        while True:
            self.search_criteria = input("\nEnter search criteria ('1' for search by pincode, '2' for search by district): ")

            if self.search_criteria is not None or self.search_criteria.strip() != "":
                self.search_criteria = int(self.search_criteria)
                if self.search_criteria in [1, 2]:
                    break
                else:
                    print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} {TextColors.UNDERLINE}{TextColors.BOLD}TIP FOR NEXT INPUT:{TextColors.ENDC} "
              f"{TextColors.BOLD}If you prefer institute with name 'Swami Ram Hospital (Garhi Cantt.)' & 'Institute Name 2' type a part of their name in lowercase letters"
              f", for example, 'ram hospit, institute name' or 'swami ram, name 2', etc. (comma-separated, without quotes){TextColors.ENDC}")
        self.institution_preferences = input("\nEnter small name for institution preference (comma-separated in case of multiple): ")

        if self.institution_preferences is not None and self.institution_preferences.strip() != "":
            self.institution_preferences = self.institution_preferences.strip().replace(', ', ',').lower().split(",")

        slot_options = ["09:00AM-11:00AM", "11:00AM-01:00PM", "01:00PM-03:00PM", "03:00PM-05:00PM"]

        while True:
            self.slot_preference = input(f"\nEnter slot preference ID (SELECT ONE) {TextColors.WARNING}[ID '1': 9AM to 11AM, ID '2': 11AM to 1PM, ID '3': 1PM to 3PM, ID '4': 3PM to 5PM]{TextColors.ENDC}: ")

            if self.slot_preference is not None or self.slot_preference.strip() != "":
                self.slot_preference = int(self.slot_preference)
                if 0 < self.slot_preference < 5:
                    self.slot_preference = slot_options[self.slot_preference - 1]
                    break
                else:
                    print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above four IDs{TextColors.ENDC}")
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above four IDs{TextColors.ENDC}")

        date = input("\nEnter appointment date to check available slots for that date (Format: dd-mm-yyyy, defaults to today if nothing is entered): ")

        if date.strip() != "":
            try:
                self.appointment_date = dt.datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')
            except ValueError:
                self.appointment_date = (dt.datetime.today()).strftime("%d-%m-%Y")
                print(f"\n{TextColors.FAIL}Incorrect date format, should have been dd-mm-yyyy. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")
        else:
            self.appointment_date = (dt.datetime.today()).strftime("%d-%m-%Y")
            print(f"\n{TextColors.FAIL}No date entered. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")

        print(f"\n-->Saving user configuration in file '{user_config_file.split('/')[-1]}'... ", end="")

        self.save_user_config(user_config_file)

        print("DONE")


    def changeAppointmentDate(self, user_config_file):
        self.use_existing_user_config(user_config_file)        # to initialise all other variables too, before calling update_user_config()

        date = input("\nEnter appointment date to check available slots for that date "
                     "(Format: dd-mm-yyyy, defaults to today if nothing is entered): ")

        if date.strip() != "":
            try:
                self.appointment_date = dt.datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')
            except ValueError:
                self.appointment_date = (dt.datetime.today()).strftime("%d-%m-%Y")
                print(f"\n{TextColors.FAIL}Incorrect date format, should have been dd-mm-yyyy. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")
        else:
            self.appointment_date = (dt.datetime.today()).strftime("%d-%m-%Y")
            print(f"\n{TextColors.FAIL}No date entered. Defaulted to today's date '{self.appointment_date}'...{TextColors.ENDC}")

        self.update_user_config(['appointment_date'], [self.appointment_date], user_config_file)


    def refreshToken(self, user_config_file, save_token_in_file=True):
        print(f"\n{TextColors.FAIL}Previous TOKEN Expired!!!{TextColors.ENDC}")

        while True:
            print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Generating OTP {TextColors.WARNING}(There might be some delay in receiving the OTP, please wait atleast 2 minutes){TextColors.ENDC}\n")

            txnId = self.generateOTP()

            otp = input("\nEnter OTP received on your mobile phone (Press 'Enter' to resend OTP): ")

            if otp is not None and otp.strip() != "":
                break

        print("\n-->\tHashing OTP to SHA256, to authenticate it in next step")

        hashed_otp = sha256(otp.encode("utf-8")).hexdigest()

        print(f"\nhashed OTP: {hashed_otp}")

        print("\n-->\tConfirming OTP and 'txnId' to get token")

        self.token = self.confirmOTP(hashed_otp, txnId)

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
                print(f"txnId: {txnId}\t(SUCCESS)")
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
        except Exception as e:
            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
            if "unauthenticated access" in response.text.lower():
                print(f"\n{TextColors.FAIL}INCORRECT OTP ENTERED!!!{TextColors.ENDC} Aborting program...")
            exit(1)

        return token


    def getStateDistrictPincodePreferences(self):
        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Getting list of all states\n")
        response = requests.request("GET", self.getStates_url, headers=self.auth_headers)

        if response.status_code == 200:
            try:
                self.display_table(response.json()['states'])

                state_id = input("\nEnter state ID: ")
                state_id = int(state_id)
                state_name = [state['state_name'] for state in response.json()['states'] if state['state_id'] == state_id][0]

                print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Getting list of all districis in '{state_name}'\n")
                response = requests.request("GET", self.getDistricts_url + "/" + str(state_id), headers=self.headers)

                if response.status_code == 200:
                    self.display_table(response.json()['districts'])

                    district_id = input("\nEnter district ID: ")
                    district_id = int(district_id)
                    district_name = [district['district_name'] for district in response.json()['districts'] if district['district_id'] == district_id][0]
                else:
                    print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: Error getting districts list){TextColors.ENDC} (response: {response.text})")
                    exit(1)
            except Exception as e:
                print(f"\n{TextColors}FAILED ATTEMPT (message: {e}){TextColors.ENDC}")
                exit(1)
        else:
            raise Exception(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: Error getting states list){TextColors.ENDC} (response: {response.text})")

        while True:
            pincode_preferences = input("\nEnter pincode preference (comma-separated in case of multiple): ")

            if pincode_preferences is not None and pincode_preferences.strip() != "":
                pincode_preferences = pincode_preferences.strip().replace(" ", "").split(",")
                pincode_preferences = [int(pincode) for pincode in pincode_preferences]
                break
            else:
                print(f"\n{TextColors.FAIL}Invalid input! Pincode can't be empty{TextColors.ENDC}")

        return state_id, state_name, district_id, district_name, pincode_preferences


    def findCentresByPin(self):
        params = {
            "pincode": self.pincode_preferences[0],
            "date": self.appointment_date,
        }

        response = requests.request("GET", self.findByPin_url, headers=self.headers, params=params)

        try:
            all_centres = response.json()['sessions']
        except Exception as e:
            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
            exit(1)

        return all_centres


    def findCentresByDistrict(self):
        params = {
            "district_id": self.district_id,
            "date": self.appointment_date,
            # "min_age_limit": 18,
            # "vaccine": "COVISHIELD"
        }

        response = requests.request("GET", self.findByDistrict_url, headers=self.headers, params=params)

        try:
            all_centres = response.json()['sessions']
        except Exception as e:
            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
            exit(1)

        return all_centres


    def findCentresBySearchCriteria(self):
        if self.search_criteria == 1:
            print(f"\n-->\tGetting list of centres for pincode '{self.pincode_preferences[0]}' (first pincode in your preferences), using date '{self.appointment_date}'")

            all_centres = self.findCentresByPin()
        else:
            print(f"\n-->\tGetting list of centres for district '{self.district_name}', using date '{self.appointment_date}'")

            all_centres = self.findCentresByDistrict()

        return all_centres


    def get_beneficiaries(self):
        response = requests.request("GET", self.beneficiaries_url, headers=self.auth_headers)

        try:
            beneficiaries = response.json()['beneficiaries']
        except Exception as e:
            print(f"{TextColors.FAIL}{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC}{TextColors.ENDC} (response: {response.text})")
            beneficiaries = None

        return beneficiaries, response.status_code


    @staticmethod
    def get_appointment_details(appointment_dict):
        appointment_details = f"{TextColors.HEADER}Apt. ID:{TextColors.ENDC} {appointment_dict['appointment_id']}\n" \
                              f"{TextColors.HEADER}Venue:{TextColors.ENDC} {appointment_dict['name']}\n" \
                              f"{TextColors.HEADER}Date:{TextColors.ENDC} {appointment_dict['date']}\n" \
                              f"{TextColors.HEADER}Slot:{TextColors.ENDC} {appointment_dict['slot']}"

        return appointment_details


    def generate_captcha(self, user_config_file):
        print(f"\n{TextColors.HEADER}========================================= GETTING CAPTCHA ========================================={TextColors.ENDC}")

        while True:
            response = requests.request("POST", self.captcha_url, headers=self.auth_headers)

            if response.status_code == 200:
                print(f"\nCAPTCHA GENERATED!!!")
                return captcha_builder(response.json())
            else:
                if "unauthenticated access" in response.text.lower():
                    self.refreshToken(user_config_file)
                else:
                    print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: could not generate captcha){TextColors.ENDC} (response: {response.text})... trying again in 1 sec.")
                    time.sleep(1)


    def isValidCentre(self, centre, min_age_limit):
        isValidPincode, isValidInstitute, isValidMinAgeSelected = False, False, False

        if self.search_criteria == 1:
            isValidPincode = True if centre['pincode'] == self.pincode_preferences[0] else False
        elif self.search_criteria == 2:
            isValidPincode = True if centre['pincode'] in self.pincode_preferences else False

        if len(self.institution_preferences) > 0:
            for institue in self.institution_preferences:
                isValidInstitute = True if institue in centre['name'].lower() else False
                if isValidInstitute:
                    break
        else:
            isValidInstitute = True             # because in case of no preference, institute name doesn't matter

        isValidMinAgeSelected = True if centre['min_age_limit'] == min_age_limit else False

        isValidCentre = isValidPincode and isValidInstitute and isValidMinAgeSelected

        return isValidCentre


    def schedule_appointment(self, all_centres, ref_ids, dose_number, min_age_limit, user_config_file):
        appointment_booked_flag = False
        appointment_id = None

        print(f"Ref. IDs to schedule booking for: {ref_ids}")

        for centre in all_centres:
            print(f"\ntrying centre '{centre['name']}'\t{TextColors.BOLD}{TextColors.WARNING}(Min Age Limit: {centre['min_age_limit']}){TextColors.ENDC}...", end=" ")

            dummy_centre_check = False
            # dummy_centre_check = 'gdmc hos' in centre['name'].lower()

            if self.isValidCentre(centre, min_age_limit) or dummy_centre_check:
                print(f"{TextColors.BOLD}{TextColors.WARNING}BOOKING{TextColors.ENDC}")
                if centre['available_capacity'] >= len(ref_ids):
                    captcha = self.generate_captcha(user_config_file)

                    print(f"{TextColors.BLACKONGREY}Entered Value: {captcha}{TextColors.ENDC}")

                    payload = json.dumps({
                        "dose": dose_number,
                        "center_id": centre['center_id'],
                        "session_id": centre['session_id'],
                        "slot": self.slot_preference,
                        "beneficiaries": ref_ids,
                        "captcha": captcha
                    })

                    response = requests.request("POST", self.schedule_url, headers=self.auth_headers, data=payload)

                    try:
                        appointment_id = response.json()['appointment_confirmation_no']
                        print(f"\n{TextColors.SUCCESS}[+]{TextColors.ENDC} SUCCESS: '{centre['name']}, {centre['address']}' centre successfully booked for {self.appointment_date} for selected beneficiaries")
                        print(f"\nAppointment Confirmation Number: {appointment_id}")
                        appointment_booked_flag = True
                        break
                    except Exception as e:
                        if "unauthenticated access" in response.text.lower():
                            self.refreshToken(user_config_file)
                        else:
                            print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
                else:
                    print(f"{TextColors.FAIL}FAILED: Vaccine shots available are less than the number of beneficiaries selected{TextColors.ENDC}")

        return appointment_booked_flag, appointment_id
