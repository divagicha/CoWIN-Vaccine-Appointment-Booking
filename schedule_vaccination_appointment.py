import os
import re
import sys
# import json
import time
import datetime as dt
from CovidVaccineChecker import TextColors, CoWINAPI


os.system("color 0F")                                   # to get screen colors when running script on shell / CMD

print(f"""
  .oooooo.             oooooo   oooooo     oooo ooooo ooooo      ooo            .o.       ooooooooo.   ooooo 
 d8P'  `Y8b             `888.    `888.     .8'  `888' `888b.     `8'           .888.      `888   `Y88. `888' 
888           .ooooo.    `888.   .8888.   .8'    888   8 `88b.    8           .8"888.      888   .d88'  888  
888          d88' `88b    `888  .8'`888. .8'     888   8   `88b.  8          .8' `888.     888ooo88P'   888  
888          888   888     `888.8'  `888.8'      888   8     `88b.8         .88ooo8888.    888          888  
`88b    ooo  888   888      `888'    `888'       888   8       `888        .8'     `888.   888          888  
 `Y8bood8P'  `Y8bod8P'       `8'      `8'       o888o o8o        `8       o88o     o8888o o888o        o888o 
""")

mobile_number_pattern = re.compile("^[6-9][0-9]{9}$")
# beneficiary_index_pattern = re.compile("^[1-4]$")
dose_and_min_age_pattern = re.compile("^[1-2]$")
vaccine_preference_pattern = re.compile("^[1-3]$")

while True:
    mobile = input("\n-->\tEnter mobile: ")

    if mobile.strip() and mobile_number_pattern.match(mobile.strip()):           # checks for None and empty string value first
        mobile = mobile.strip()
        break
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter correct mobile number (rule: 10-digit number starting with either 6,7,8 or 9){TextColors.ENDC}")

cowinAPI = CoWINAPI(mobile)

if not os.path.exists(os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/")):
    os.makedirs(os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/"))

# if not os.path.exists(os.path.join(cowinAPI.BASE_PROJECT_DIR, "captcha/")):
#     os.makedirs(os.path.join(cowinAPI.BASE_PROJECT_DIR, "captcha/"))

user_config_file = os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/user_config_" + mobile + ".json")

if os.path.exists(user_config_file):
    print(f"\nUser configuration file found for '{mobile}'! Listing details...\n")

    cowinAPI.displayConfigFileData(user_config_file)

    while True:
        answer = input(f"\n-->\tReady to go? {TextColors.WARNING}(Continue with existing configuration (y) / "
                       f"Create new configuration (n) / Change appointment date (c) / \n"
                       f"\t\t\t\t  Change search criteria (s) / Change slot preference (t) / Quit (q)){TextColors.ENDC}: ")

        if answer.lower().strip() == 'y':
            cowinAPI.use_existing_user_config(user_config_file)
            if not cowinAPI.is_appointment_date_valid():
                print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Incorrect Appointment Date found in configuration! Kindly change the appointment date to proceed...")
                cowinAPI.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
            break
        elif answer.lower().strip() == 'n':
            cowinAPI.create_new_user_config(user_config_file)
            break
        elif answer.lower().strip() == 'c':
            cowinAPI.changeAppointmentDate(user_config_file)
        elif answer.lower().strip() == 's':
            cowinAPI.changeSearchCriteria(user_config_file)
        elif answer.lower().strip() == 't':
            cowinAPI.changeSlotPreference(user_config_file)
        elif answer.lower().strip() == 'q':
            print(f"\nExiting program...")
            exit(0)
        else:
            print(f"\n{TextColors.FAIL}Invalid input!{TextColors.ENDC}")
else:
    print("\nUser configuration file not found! Creating new user configuration...")

    cowinAPI.create_new_user_config(user_config_file)

while True:
    print(f"\n-->\tGetting beneficiaries registered with mobile number '{mobile}'\n")

    beneficiaries, response_statusCode = cowinAPI.get_beneficiaries()

    if response_statusCode == 200:
        break
    else:
        cowinAPI.generateUserToken(user_config_file, refresh_token=True)

if not beneficiaries or len(beneficiaries) == 0:
    print(f"{TextColors.FAIL}No beneficiaries have been added in this account! Kindly add one or more (max. 4) "
          f"beneficiaries first by going to link https://selfregistration.cowin.gov.in/ and then run the script again.{TextColors.ENDC}")
    exit(1)

current_year = dt.datetime.today().year
beneficiaries_list = [{"Ref. ID": beneficiary['beneficiary_reference_id'],
                       "Name": beneficiary['name'],
                       "Gender": beneficiary['gender'],
                       "Age": current_year - int(beneficiary['birth_year']),
                       "Vaccination Status": cowinAPI.get_vaccination_status_details(beneficiary['vaccination_status'], beneficiary['dose1_date'], beneficiary['dose2_date']),
                       "Appointment Details (Dose 1)": cowinAPI.get_appointment_details(beneficiary['appointments'][0]) if len(beneficiary['appointments']) > 0 else "-",
                       "Appointment Details (Dose 2)": cowinAPI.get_appointment_details(beneficiary['appointments'][1]) if len(beneficiary['appointments']) > 1 else "-"}
                      for beneficiary in beneficiaries]

cowinAPI.display_table(beneficiaries_list)

# print(json.dumps(beneficiaries, indent=4))

print(f"\n{TextColors.BLACKONGREY}Total Beneficiaries Found: {len(beneficiaries)}{TextColors.ENDC}")

while True:
    ids_input = input(f"\nEnter comma-separated index of beneficiaries to schedule appointment for {TextColors.WARNING}(Enter '0' to select all or 'q' to quit and try after sometime){TextColors.ENDC}: ")

    if not ids_input.strip():           # checks for None and empty string value
        print(f"\n{TextColors.FAIL}Please enter correct indexes to proceed to booking. This value can't be empty{TextColors.ENDC}")
        continue
    elif ids_input.strip().lower() == 'q':
        print("\nExiting program...")
        exit(0)
    elif ids_input.strip() == '0':
        reference_ids = [beneficiary['beneficiary_reference_id'] for beneficiary in beneficiaries]
        break
    elif '0' in ids_input.strip() or 'q' in ids_input.strip().lower():
        print(f"\n{TextColors.FAIL}Please enter correct indexes to proceed to booking. Don't club '0' or 'q' with any other option{TextColors.ENDC}")
        continue
    else:
        reference_ids = ids_input.strip().replace(" ", "").split(",")
        reference_ids = list(filter(None, reference_ids))                   # to filter out all empty strings
        # beneficiary_index_pattern = re.compile("^[1-4]$")
        regex_pattern = f"^[1-{len(beneficiaries)}]$"
        beneficiary_index_pattern = re.compile(regex_pattern)
        areValidIndexes = [bool(beneficiary_index_pattern.match(index)) for index in reference_ids]
        if False in areValidIndexes or len(areValidIndexes) == 0:
            print(f"\n{TextColors.FAIL}Please enter correct indexes to proceed to booking{TextColors.ENDC}")
            continue

    reference_ids = list(map(lambda x: int(x)-1, reference_ids))
    reference_ids = [beneficiaries[index]['beneficiary_reference_id'] for index in reference_ids]
    break

while True:
    dose_number = input(f"\nEnter dose number for selected beneficiaries {TextColors.WARNING}(SELECT ONE) ['1' for Dose 1, '2' for Dose 2]{TextColors.ENDC}: ")

    if dose_number.strip() and dose_and_min_age_pattern.match(dose_number.strip()):           # checks for None and empty string value first
        dose_number = int(dose_number.strip())
        break
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

while True:
    min_age_limit = input(f"\nEnter min age limit for selected beneficiaries {TextColors.WARNING}(SELECT ONE) ['1' for 18+, '2' for 45+]{TextColors.ENDC}: ")

    if min_age_limit.strip() and dose_and_min_age_pattern.match(min_age_limit.strip()):           # checks for None and empty string value first
        min_age_limit = int(min_age_limit.strip())
        min_age_limit = 18 if min_age_limit == 1 else 45
        break
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

while True:
    vaccine_preference = input(f"\nEnter vaccine preference for selected beneficiaries {TextColors.WARNING}(SELECT ONE) ['1' for '-ANY-', '2' for 'COVAXIN', '3' for 'COVISHIELD']{TextColors.ENDC}: ")

    if vaccine_preference.strip() and vaccine_preference_pattern.match(vaccine_preference.strip()):           # checks for None and empty string value first
        vaccine_preference = int(vaccine_preference.strip())
        vaccine_preference = '' if vaccine_preference == 1 else 'covaxin' if vaccine_preference == 2 else 'covishield'
        break
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above three choices{TextColors.ENDC}")

print(f"\n-->\tAttempting to book appointment {TextColors.WARNING}(every 3 seconds for next 4 minutes, i.e., total 80 attempts)"
      f"{TextColors.ENDC}")

# input(f"\n{TextColors.BOLD}Note: keep an eye on the screen when the process starts, as when a valid centre "
#       f"gets available you will be asked to enter {TextColors.WARNING}captcha{TextColors.ENDC} {TextColors.BOLD}and select "
#       f"{TextColors.WARNING}time slot{TextColors.ENDC} {TextColors.BOLD}to book and confirm the appointment{TextColors.ENDC}"
#       f"\n\nPress 'Enter' to continue...")
input(f"\n{TextColors.BOLD}Note: keep an eye on the screen when the process starts, as when a valid centre "
      f"gets available you will be asked to select a {TextColors.WARNING}time slot{TextColors.ENDC} "
      f"{TextColors.BOLD}to book and confirm the appointment{TextColors.ENDC}\n\nPress 'Enter' to continue...")

if not cowinAPI.is_appointment_date_valid():
    print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Incorrect Appointment Date found in configuration! Kindly change the appointment date to proceed...")
    cowinAPI.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
    print("")

all_centres = cowinAPI.findCentresBySearchCriteria()

if len(all_centres) == 0:
    print(f"{TextColors.FAIL}No Centre Found{TextColors.ENDC} (Either all centres are fully booked for the selected appointment date or "
          f"slots aren't opened yet. You can continue with the same configuration or try changing date or search criteria)")

    print(f"\n{TextColors.BOLD}Note: Continue with existing configuration only if you are sure that slots are gonna open "
          f"in few minutes!{TextColors.ENDC}")
    while True:
        answer = input(f"\n-->\tEnter choice {TextColors.WARNING}(Continue with existing configuration (y) / "
                       f"Change appointment date (c) / Change search criteria (s)){TextColors.ENDC}: ")

        if answer.lower().strip() == 'y':
            if not cowinAPI.is_appointment_date_valid():
                print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Incorrect Appointment Date found in configuration! Kindly change the appointment date to proceed...")
                cowinAPI.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
                print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Continuing with updated configuration", end="")
            else:
                print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Continuing with existing configuration", end="")
            break
        elif answer.lower().strip() == 'c':
            cowinAPI.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
            print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Appointment date changed successfully")
            # break
        elif answer.lower().strip() == 's':
            cowinAPI.changeSearchCriteria(user_config_file, load_values_from_existing_config_first=False)
            print(f"\n{TextColors.WARNING}[+]{TextColors.ENDC} Search criteria changed successfully")
            # break
        else:
            print(f"\n{TextColors.FAIL}Invalid input! Please enter a valid option to continue{TextColors.ENDC}")
else:
    # centres_list = [{"Name": centre['name'], "District": centre['district_name'], "Pincode": centre['pincode'], "Vaccine Name": centre['vaccine'],
    #                  "Fee Type": centre['fee_type'], "Min Age": centre['min_age_limit'], "Available Capacity": centre['available_capacity'],
    #                  "Slots": "\n".join(centre['slots'])} for centre in all_centres]
    #
    # cowinAPI.display_table(centres_list)

    print(f"\n{TextColors.BLACKONGREY}Total Centres Found: {len(all_centres)}{TextColors.ENDC}", end="")

attempts = 0
appointment_booked_flag = False

while True:
    try:
        if attempts < 80:
            print(f"\n\n{TextColors.UNDERLINE}{TextColors.BOLD}ATTEMPT {attempts+1}:{TextColors.ENDC}")
            appointment_booked_flag, appointment_id = cowinAPI.schedule_appointment(all_centres, reference_ids, dose_number, min_age_limit, vaccine_preference, user_config_file)

            if appointment_booked_flag:
                break

            attempts += 1
            time.sleep(1)

            print(f"\n\n[+] Updating all_centres list to refresh "
                  f"available_capacity value for each centre before next attempt", flush=True)
            sys.stdout.flush()
            time.sleep(1)
            all_centres = cowinAPI.findCentresBySearchCriteria()
            if len(all_centres) > 0:
                print(f"{TextColors.BLACKONGREY}Total Centres Found: {len(all_centres)}{TextColors.ENDC}", end="")
            else:
                print(f"{TextColors.FAIL}No Centre Found{TextColors.ENDC} (Either all centres are fully booked for the selected appointment date or slots aren't opened yet. "
                      f"You can also try running the script again after changing date, search criteria, district or pincode)", end="")
            time.sleep(1)
        else:
            break
    except KeyboardInterrupt:
        print(f"\n{TextColors.FAIL}(FAILED: Scheduling interrupted by user){TextColors.ENDC}")
        input("\nPress any key to exit...")
        exit(1)

if not appointment_booked_flag:
    print(f"\n{TextColors.FAIL}FAILED: Appointment could not be scheduled, as no valid slot found to be available. Please try again after 1 minute.{TextColors.ENDC}")
else:
    print(f"\n{TextColors.SUCCESS}Hurray!! Your appointment has been successfully scheduled. Following are the details:\n\n"
          f"Apt. ID: {appointment_id}\n"
          f"Centre: {cowinAPI.appointment_centre_booked}\n"
          f"Date: {cowinAPI.appointment_date}\n"
          f"Slot: {cowinAPI.appointment_slot_selected}{TextColors.ENDC}")
    input("\nPress any key to exit...")
    exit(1)
