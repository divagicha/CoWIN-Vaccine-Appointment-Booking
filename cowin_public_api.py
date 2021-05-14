import requests
import json
from hashlib import sha256
import time
from configparser import ConfigParser
import datetime as dt
import pickle
import os

config = ConfigParser()
config_file = "user_data.INI"
session_file = "session.pkl"

appointment_date = "14-05-2021"
slot = "03:00PM-05:00PM"
beneficiaries = [
    "27958710946560",
    "96852936531390",
    "16765697648940",
    "42824675561870"
]

base_url = "https://cdn-api.co-vin.in/api/v2"

generateOTP_url = base_url + "/auth/public/generateOTP"
confirmOTP_url = base_url + "/auth/public/confirmOTP"
findByDistrict_url = base_url + "/appointment/sessions/public/findByDistrict"
schedule_url = base_url + "/appointment/schedule"

answer = input("\nCreate new user (y) / Use previous data (n): ")

if answer.lower() == 'y':
    mobile = input("\n-->\tEnter mobile: ")

    session = requests.Session()

    print(f"\n-->\tUsing mobile number: {mobile}, appointment_date: {appointment_date}")
    headers = {
      'Content-Type': 'application/json'
    }
    payload = json.dumps({
      "mobile": mobile
    })
    print("\n-->\tGetting 'txnId' to authenticate OTP in next step\n")
    while True:
        response = session.request("POST", generateOTP_url, headers=headers, data=payload)
        time_now = dt.datetime.now()
        txnDate = time_now.strftime("%d-%m-%Y")
        txnTime = time_now.strftime("%H:%M:%S")

        try:
            txnId = response.json()['txnId']
            print(f"txnId: {txnId}\t(SUCCESS)")
            break
        except Exception as e:
            print(f"FAILED ATTEMPT (message: {e}) ...trying again after 3 seconds")
            pass

        time.sleep(3)

    otp = input("\n-->\tKindly enter OTP received on your mobile phone: ")

    print("\n-->\tHashing OTP to SHA256, to authenticate it in next step")
    hashed_otp = sha256(otp.encode("utf-8")).hexdigest()

    print(f"\nhashed OTP: {hashed_otp}")

    print("\n-->\tConfirming OTP and 'txnId' to get token")
    headers = {
      'Content-Type': 'application/json'
    }
    payload = json.dumps({
      "otp": hashed_otp,
      "txnId": txnId
    })

    response = session.request("POST", confirmOTP_url, headers=headers, data=payload)

    try:
        token = response.json()["token"]
        print(f"\nresponse token obtained: {token}")
    except Exception as e:
        print(f"\nFAILED ATTEMPT (message: {e}) (response: {response.text})")
        exit(1)

    # print(f"\nCookies dictionary: {session.cookies.get_dict()}")
    # print(f"\nSession ID: {session.cookies.get('SESSIONID')}")

    state_id = 35
    # "state_name": "Uttarakhand"
    district_id = 697
    # "district_name": "Dehradun"

    print("\n-->\tGetting centres list for Dehradun district")
    headers = {
        'Accept-Language': 'hi_IN',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'
    }
    params = {
        "district_id": district_id,
        "date": appointment_date,
        # "min_age_limit": 18,
        # "vaccine": "COVISHIELD"
    }
    payload = {}

    response = session.request("GET", findByDistrict_url, headers=headers, params=params, data=payload)

    try:
        all_centres = response.json()['sessions']
    except Exception as e:
        print(f"\nFAILED ATTEMPT (message: {e}) (response: {response.text})")
        exit(1)

    centre_names = [centre['name'] for centre in all_centres]
    centre_names = "\n".join([f'{i+1}. {name}' for i, name in enumerate(centre_names)])
    print(f"\nCentres Found:\n{centre_names}")
    print(f"\nTotal Centres: {len(all_centres)}")


    print("\n-->\tAttempting to book appointment")
    # pincode: 248140 (GANPATI WEDDING P. BHANIYAWALA)
    # pincode: 249201 (RAJKIYA M VIDHYALAYA RISHIKESH)
    appointment_booked_flag = False

    for centre in all_centres:
        print(f"\ntrying centre '{centre['name']}'...", end=" ")
        centre_is_rishikesh = centre['pincode'] == 249201 and (centre['name']).lower().contains('rajkiya m')
        centre_is_bhaniyawala = centre['pincode'] == 248140 and (centre['name']).lower().contains('ganpati wedding')

        if centre_is_rishikesh or centre_is_bhaniyawala:
            print("BOOKING", end="")
            if centre['available_capacity'] > 0:
                payload = json.dumps({
                    "dose": 1,
                    "session_id": centre['session_id'],
                    "slot": slot,
                    "beneficiaries": beneficiaries
                })
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

                response = requests.request("POST", schedule_url, headers=headers, data=payload)

                try:
                    appointment_id = response.json()['appointment_id']
                    print("\t(SUCCESS)")
                    print(f"\nAppointment ID: {appointment_id}")
                    appointment_booked_flag = True
                    break
                except Exception as e:
                    print(f"\tFAILED ATTEMPT (message: {e}) (response: {response.text})")
                    exit(1)

    if not appointment_booked_flag:
        print("\n(FAILED: Appointment could not be booked)")

    print("\n-->\tSaving session in pickle file")
    if os.path.exists(session_file):
        os.remove(session_file)
    with open(session_file, 'wb') as f:
        pickle.dump(session.cookies, f)

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
    config.read(config_file)

    mobile = config.get('USER', 'mobile')
    txnDate = config.get('USER', 'txnDate')
    token = config.get('USER', 'token')
    otp = config.get('USER', 'otp')
    district_id = config.get('USER', 'district_id')

    print(f"\nmobile: {mobile}, txnDate: {txnDate}, OTP: {otp}, district_id: {district_id}, appointment_date: {appointment_date}")

    try:
        print("\n-->\tGetting session cookies data from pickle file...", end=" ")
        session = requests.Session()
        with open(session_file, 'rb') as f:
            session.cookies.update(pickle.load(f))
        print("DONE")
    except IOError:
        print("FAILED")
        print("\nERROR LOADING PAST SESSION COOKIES! Using new session...")

    print("\n-->\tGetting centres list for Dehradun district")
    headers = {
        'Accept-Language': 'hi_IN',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'
    }
    params = {
        "district_id": district_id,
        "date": appointment_date,
        # "min_age_limit": 18,
        # "vaccine": "COVISHIELD"
    }
    payload = {}

    response = session.request("GET", findByDistrict_url, headers=headers, params=params, data=payload)

    try:
        all_centres = response.json()['sessions']
    except Exception as e:
        print(f"\nFAILED ATTEMPT (message: {e}) (response: {response.text})")
        exit(1)

    centre_names = [centre['name'] for centre in all_centres]
    centre_names = "\n".join([f'{i+1}. {name}' for i, name in enumerate(centre_names)])
    print(f"\nCentres Found:\n{centre_names}")
    print(f"\nTotal Centres: {len(all_centres)}")


    print("\n-->\tAttempting to book appointment")
    # pincode: 248140 (GANPATI WEDDING P. BHANIYAWALA)
    # pincode: 249201 (RAJKIYA M VIDHYALAYA RISHIKESH)
    appointment_booked_flag = False

    for centre in all_centres:
        print(f"\ntrying centre '{centre['name']}'...", end=" ")
        centre_is_rishikesh = centre['pincode'] == 249201 and (centre['name']).lower().contains('rajkiya m')
        centre_is_bhaniyawala = centre['pincode'] == 248140 and (centre['name']).lower().contains('ganpati wedding')

        if centre_is_rishikesh or centre_is_bhaniyawala:
            print("BOOKING", end="")
            if centre['available_capacity'] > 0:
                payload = json.dumps({
                    "dose": 1,
                    "session_id": centre['session_id'],
                    "slot": slot,
                    "beneficiaries": beneficiaries
                })
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

                response = requests.request("POST", schedule_url, headers=headers, data=payload)

                try:
                    appointment_id = response.json()['appointment_id']
                    print("\t(SUCCESS)")
                    print(f"\nAppointment ID: {appointment_id}")
                    appointment_booked_flag = True
                    break
                except Exception as e:
                    print(f"\tFAILED ATTEMPT (message: {e}) (response: {response.text})")
                    exit(1)

    if not appointment_booked_flag:
        print("\n(FAILED: Appointment could not be booked)")
