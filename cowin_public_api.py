import os
import re
import sys
import json
import time
import requests
# import pickle
import tabulate
import datetime as dt
from hashlib import sha256
from captcha import captcha_builder
from configparser import ConfigParser


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
    

os.system("color FF")                       # to get screen colors when running script on CMD

config = ConfigParser()
config_file = "user_data.INI"
# session_file = "session.pkl"

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
secret = "U2FsdGVkX1+LQcQNX+RTIipW+jdFWg02BOScu2dJksHYVYzKd3h2oAbeECbhE4SrYB0JIkVLHf4cSdxK7uSmiA=="
headers = {
    'User-Agent': user_agent,
    # 'Content-Type': 'application/json'
}
auth_headers = {
    'Authorization': None,
    'User-Agent': user_agent,
    # 'Content-Type': 'application/json'
}

appointment_date = "17-05-2021"
slot = "03:00PM-05:00PM"

base_url = "https://cdn-api.co-vin.in/api/v2"

# generateOTP_public_url = base_url + "/auth/public/generateOTP"
# confirmOTP_public_url = base_url + "/auth/public/confirmOTP"
generateOTP_url = base_url + "/auth/generateMobileOTP"
confirmOTP_url = base_url + "/auth/validateMobileOtp"
findByDistrict_url = base_url + "/appointment/sessions/public/findByDistrict"
beneficiaries_url = base_url + "/appointment/beneficiaries"
schedule_url = base_url + "/appointment/schedule"
captcha_url = base_url + "/auth/getRecaptcha"


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


def generateOTP():
    payload = json.dumps({
        "mobile": mobile,
        "secret": secret
    })

    while True:
        response = requests.request("POST", generateOTP_url, headers=headers, data=payload)
        time_now = dt.datetime.now()
        txnDate = time_now.strftime("%d-%m-%Y")
        txnTime = time_now.strftime("%H:%M:%S")

        try:
            txnId = response.json()['txnId']
            print(f"txnId: {txnId}\t(SUCCESS)")
            break
        except Exception as e:
            print(f"{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})...trying again after 3 seconds")
            pass

        time.sleep(3)

    return txnId, txnDate, txnTime


def confirmOTP():
    payload = json.dumps({
      "otp": hashed_otp,
      "txnId": txnId
    })

    response = requests.request("POST", confirmOTP_url, headers=headers, data=payload)

    try:
        token = response.json()["token"]
        print(f"\nTOKEN OBTAINED: {token}")
    except Exception as e:
        print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
        exit(1)

    return token


def findCentresByDistrict():
    params = {
        "district_id": district_id,
        # "district_id": 704,                     # 702 - Haridwar, 704 - Almora
        "date": appointment_date,
        # "min_age_limit": 18,
        # "vaccine": "COVISHIELD"
    }
    payload = {}

    response = requests.request("GET", findByDistrict_url, headers=headers, params=params, data=payload)

    try:
        all_centres = response.json()['sessions']
    except Exception as e:
        print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
        exit(1)

    return all_centres


def get_beneficiaries():
    response = requests.request("GET", beneficiaries_url, headers=auth_headers)

    try:
        beneficiaries = response.json()['beneficiaries']
    except Exception as e:
        print(f"{TextColors.FAIL}{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC}{TextColors.ENDC} (response: {response.text})")
        beneficiaries = None
        # exit(1)

    # beneficiaries = [{"beneficiary_reference_id": beneficiary['beneficiary_reference_id'], "name": beneficiary['name']} for beneficiary in beneficiaries]

    return beneficiaries, response.status_code


def get_apt_details(appointment_dict):
    appointment_details = f"{TextColors.HEADER}Apt. ID:{TextColors.ENDC} {appointment_dict['appointment_id']}\n" \
                          f"{TextColors.HEADER}Venue:{TextColors.ENDC} {appointment_dict['name']}\n" \
                          f"{TextColors.HEADER}Date:{TextColors.ENDC} {appointment_dict['date']}\n" \
                          f"{TextColors.HEADER}Slot:{TextColors.ENDC} {appointment_dict['slot']}"

    return appointment_details


def generate_captcha():
    print("\n========================================= GETTING CAPTCHA =========================================")

    response = requests.request("POST", captcha_url, headers=auth_headers)

    if response.status_code == 200:
        print(f"\nCAPTCHA GENERATED!!!")
        # with open("captcha_response.json", "w") as f:
        #     f.write(json.dumps(json.loads(response.text), indent=4))
        return captcha_builder(response.json())
    else:
        print(f"\n{TextColors.FAIL}{TextColors.FAIL}FAILED ATTEMPT {TextColors.ENDC}{TextColors.ENDC} (response: {response.text})")
        exit(1)


def schedule_appointment(ref_ids):
    # pincode: 248140 (GANPATI WEDDING P. BHANIYAWALA)
    # pincode: 249201 (RAJKIYA M VIDHYALAYA RISHIKESH)
    appointment_booked_flag = False
    appointment_id = None

    print(f"Ref. IDs to schedule booking for: {ref_ids}")

    for centre in all_centres:
        print(f"\ntrying centre '{centre['name']}'\t{TextColors.BOLD}{TextColors.WARNING}(Min Age Limit: {centre['min_age_limit']}){TextColors.ENDC}...", end=" ")
        centre_is_rishikesh = centre['pincode'] == 249201 and 'rajkiya m' in centre['name'].lower() and centre['min_age_limit'] == 18
        centre_is_bhaniyawala = centre['pincode'] == 248140 and 'ganpati wedding' in centre['name'].lower() and centre['min_age_limit'] == 18
        # centre_is_bhaniyawala = 'office laksar' in centre['name'].lower() and centre['min_age_limit'] == 18

        if centre_is_rishikesh or centre_is_bhaniyawala:
            print(f"{TextColors.BOLD}{TextColors.WARNING}BOOKING{TextColors.ENDC}")
            if centre['available_capacity'] >= len(ref_ids):                # > 3 because we have to book for 4 beneficiaries
                captcha = generate_captcha()
                print(f"{TextColors.BLACKONGREY}Entered Value: {captcha}{TextColors.ENDC}")

                payload = json.dumps({
                    "dose": 1,
                    "center_id": centre['center_id'],
                    "session_id": centre['session_id'],
                    "slot": slot,
                    "beneficiaries": ref_ids,
                    "captcha": captcha
                })

                response = requests.request("POST", schedule_url, headers=auth_headers, data=payload)

                try:
                    appointment_id = response.json()['appointment_confirmation_no']
                    print(f"\n{TextColors.SUCCESS}[+]{TextColors.ENDC} SUCCESS: '{centre['name']}, {centre['address']}' centre booked for {appointment_date}")
                    print(f"\nAppointment Confirmation Number: {appointment_id}")
                    appointment_booked_flag = True
                    break
                except Exception as e:
                    print(f"\n{TextColors.FAIL}FAILED ATTEMPT (message: {e}){TextColors.ENDC} (response: {response.text})")
                    # exit(1)
            else:
                print(f"{TextColors.FAIL}FAILED: Slots available are less than the number of beneficiaries selected{TextColors.ENDC}")

    return appointment_booked_flag, appointment_id


"""
-----------------------------------------------------------------------------
------------------------------ MAIN CODE START ------------------------------
-----------------------------------------------------------------------------
"""

answer = input(f"\n{TextColors.WARNING}Create new user (y) / Use previous data (n):{TextColors.ENDC} ")

if answer.lower() == 'y':
    mobile = input("\n-->\tEnter mobile: ")

    # session = requests.Session()

    print(f"\n-->\tUsing mobile number: {mobile}, appointment_date: {appointment_date}")

    print("\n-->\tGenerating OTP for entered mobile number\n")

    txnId, txnDate, txnTime = generateOTP()

    otp = input("\n-->\tKindly enter OTP received on your mobile phone: ")

    print("\n-->\tHashing OTP to SHA256, to authenticate it in next step")

    hashed_otp = sha256(otp.encode("utf-8")).hexdigest()

    print(f"\nhashed OTP: {hashed_otp}")

    print("\n-->\tConfirming OTP and 'txnId' to get token")

    token = confirmOTP()

    # print(f"\nCookies dictionary: {session.cookies.get_dict()}")
    # print(f"\nSession ID: {session.cookies.get('SESSIONID')}")

    state_id = 35
    # "state_name": "Uttarakhand"
    district_id = 697
    # "district_name": "Dehradun"

    # print("\n-->\tSaving session in pickle file")
    # if os.path.exists(session_file):
    #     os.remove(session_file)
    # with open(session_file, 'wb') as f:
    #     pickle.dump(session.cookies, f)

    print("\n-->\tSaving config file")
    if os.path.exists(config_file):
        os.remove(config_file)
    config.add_section('USER')
    config.set('USER', 'mobile', mobile)
    config.set('USER', 'txnDate', txnDate)
    config.set('USER', 'txnTime', txnTime)
    config.set('USER', 'txnId', txnId)
    config.set('USER', 'otp', otp)
    config.set('USER', 'hashed_otp', hashed_otp)
    config.set('USER', 'token', token)
    config.set('USER', 'state_id', str(state_id))
    config.set('USER', 'district_id', str(district_id))
    with open(config_file, 'w') as configfile_handle:
        config.write(configfile_handle)
else:
    print("\n-->\tReading contents from config file")

    if not os.path.exists(config_file):
        print("\nFAILED!!! Config file 'user_data.INI' does not exist.")
        exit(1)

    config.read(config_file)

    mobile = config.get('USER', 'mobile')
    txnDate = config.get('USER', 'txnDate')
    token = config.get('USER', 'token')
    otp = config.get('USER', 'otp')
    district_id = config.get('USER', 'district_id')

    print(f"\nmobile: {mobile}, txnDate: {txnDate}, OTP: {otp}, district_id: {district_id}, appointment_date: {appointment_date}")

    print(f"\nUsing TOKEN: {token}")

    # try:
    #     print("\n-->\tGetting session cookies data from pickle file...", end=" ")
    #     session = requests.Session()
    #     with open(session_file, 'rb') as f:
    #         session.cookies.update(pickle.load(f))
    #     print("DONE")
    # except IOError:
    #     print("FAILED")
    #     print("\nERROR LOADING PAST SESSION COOKIES! Using new session...")

print("\n-->\tGetting list of centres for Dehradun district\n")

all_centres = findCentresByDistrict()

if len(all_centres) == 0:
    print(f"{TextColors.FAIL}FAILED: All centres are fully booked for the selected appointment date. "
          f"Try running the script again after changing date or district.{TextColors.ENDC}")

# centre_names = [centre['name'] for centre in all_centres]
# centre_names = "\n".join([f'{i+1}. {name}' for i, name in enumerate(centre_names)])
# print(f"\n{TextColors.BLACKONGREY}Centres Found:\n{centre_names}{TextColors.ENDC}")
centres_list = [{"Name": centre['name'], "District": centre['district_name'], "Pincode": centre['pincode'], "Vaccine Name": centre['vaccine'],
                 "Fee Type": centre['fee_type'], "Min Age": centre['min_age_limit'], "Available Capacity": centre['available_capacity'],
                 "Slots": "\n".join(centre['slots'])} for centre in all_centres]
display_table(centres_list)
print(f"\n{TextColors.BLACKONGREY}Total Centres Found: {len(all_centres)}{TextColors.ENDC}")

tokenModified_flag = False
while True:
    print("\n-->\tGetting beneficiaries registered with above mobile number\n")

    auth_headers['Authorization'] = f'Bearer {token}'

    beneficiaries, response_statusCode = get_beneficiaries()

    if response_statusCode == 200:
        if tokenModified_flag:
            config.set('USER', 'token', token)
            with open(config_file, 'w') as configfile_handle:
                config.write(configfile_handle)
        break
    else:
        print(f"\n{TextColors.FAIL}Previous TOKEN Expired!!!{TextColors.ENDC}")
        print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Generating new OTP and Token\n")

        txnId, txnDate, txnTime = generateOTP()

        otp = input("\n-->\tKindly enter OTP received on your mobile phone: ")

        print("\n-->\tHashing OTP to SHA256, to authenticate it in next step")

        hashed_otp = sha256(otp.encode("utf-8")).hexdigest()

        print(f"\nhashed OTP: {hashed_otp}")

        print("\n-->\tConfirming OTP and 'txnId' to get token")

        token = confirmOTP()
        tokenModified_flag = True

# beneficiary_data = "\n".join([f"{i+1}. {beneficiary['name']}\t\t(Ref. ID: {beneficiary['beneficiary_reference_id']})" for i, beneficiary in enumerate(beneficiaries)])
# print(f"\n{TextColors.BLACKONGREY}Beneficiaries Found:\n{beneficiary_data}{TextColors.ENDC}")
beneficiaries_list = [{"Ref. ID": beneficiary['beneficiary_reference_id'],
                       "Name": beneficiary['name'],
                       "Gender": beneficiary['gender'],
                       "Vaccination Status": beneficiary['vaccination_status'],
                       "Appointments": get_apt_details(beneficiary['appointments'][0]) if len(beneficiary['appointments']) > 0 else "-"}
                      for beneficiary in beneficiaries]
display_table(beneficiaries_list)
print(f"\n{TextColors.BLACKONGREY}Total Beneficiaries Found: {len(beneficiaries)}{TextColors.ENDC}")

ids_input = input(f"\nEnter comma-separated index of beneficiaries to schedule appointment for {TextColors.WARNING}(Enter '0' to select all){TextColors.ENDC}: ")

while True:
    assert ids_input is not None and ids_input != ""
    reference_ids = ids_input.replace(" ", "").split(",")

    if not isinstance(reference_ids[0], int):
        reference_ids = [int(id) for id in reference_ids]
    if reference_ids[0] == 0:
        reference_ids = [beneficiary['beneficiary_reference_id'] for beneficiary in beneficiaries]
        break
    else:
        correct_ids_entered_flag = True
        reference_ids = [id-1 for id in reference_ids if 0 < id <= len(beneficiaries)]
        reference_ids = [beneficiary['beneficiary_reference_id'] for idx, beneficiary in enumerate(beneficiaries) if idx in reference_ids]

        if len(reference_ids) == 0:
            print(f"\n{TextColors.FAIL}Please enter correct indexes to proceed to booking{TextColors.ENDC}")
            ids_input = input(f"\nEnter comma-separated index of beneficiaries to schedule appointment for {TextColors.WARNING}(Enter '0' to select all){TextColors.ENDC}: ")
        else:
            break

print("\n-->\tAttempting to book appointment (every 3 seconds till 80 attempts)", end="")

attempts = 0

while True:
    try:
        if attempts < 80:
            print(f"\n\n{TextColors.UNDERLINE}{TextColors.BOLD}ATTEMPT {attempts+1}:{TextColors.ENDC}")
            appointment_booked_flag, appointment_id = schedule_appointment(reference_ids)

            if appointment_booked_flag:
                break

            attempts += 1
            time.sleep(1)

            print(f"\n\n{TextColors.WARNING}[+]{TextColors.ENDC} Updating all_centres list to refresh "
                  f"available_capacity value for each centre before next attempt", flush=True)
            sys.stdout.flush()
            time.sleep(1)
            all_centres = findCentresByDistrict()
            print(f"{TextColors.BLACKONGREY}Total Centres Found: {len(all_centres)}{TextColors.ENDC}", end="")
            time.sleep(1)
        else:
            break
    except KeyboardInterrupt:
        print(f"\n{TextColors.FAIL}(FAILED: Scheduling interrupted by user){TextColors.ENDC}")
        exit(1)

if not appointment_booked_flag:
    print(f"\n{TextColors.FAIL}FAILED: Appointment could not be booked{TextColors.ENDC}")
