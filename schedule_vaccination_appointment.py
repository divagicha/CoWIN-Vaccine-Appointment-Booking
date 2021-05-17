import os
import re
import sys
# import json
import time
from CovidVaccineChecker import TextColors, CoWINAPI


os.system("color FF")                                   # to get screen colors when running script on shell / CMD

print("""
  .oooooo.             oooooo   oooooo     oooo ooooo ooooo      ooo            .o.       ooooooooo.   ooooo 
 d8P'  `Y8b             `888.    `888.     .8'  `888' `888b.     `8'           .888.      `888   `Y88. `888' 
888           .ooooo.    `888.   .8888.   .8'    888   8 `88b.    8           .8"888.      888   .d88'  888  
888          d88' `88b    `888  .8'`888. .8'     888   8   `88b.  8          .8' `888.     888ooo88P'   888  
888          888   888     `888.8'  `888.8'      888   8     `88b.8         .88ooo8888.    888          888  
`88b    ooo  888   888      `888'    `888'       888   8       `888        .8'     `888.   888          888  
 `Y8bood8P'  `Y8bod8P'       `8'      `8'       o888o o8o        `8       o88o     o8888o o888o        o888o 
""")

mobile_number_pattern = re.compile("[7-9][0-9]{9}")

while True:
    mobile = input("\n-->\tEnter mobile: ")

    if mobile is not None and mobile.strip() != "" and mobile_number_pattern.match(mobile.strip()):
        mobile = mobile.strip()
        break
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter correct mobile number (format: 10-digit number starting with either 7,8 or 9){TextColors.ENDC}")

cowinAPI = CoWINAPI(mobile)

if not os.path.exists(os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/")):
    os.makedirs(os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/"))

if not os.path.exists(os.path.join(cowinAPI.BASE_PROJECT_DIR, "captcha/")):
    os.makedirs(os.path.join(cowinAPI.BASE_PROJECT_DIR, "captcha/"))

user_config_file = os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/user_config_" + mobile + ".json")

if os.path.exists(user_config_file):
    print(f"\nUser configuration file found for '{mobile}'! Listing details...\n")

    cowinAPI.displayConfigFileData(user_config_file)

    while True:
        answer = input(f"\n-->\tReady to go? {TextColors.WARNING}(Continue with existing configuration (y) / "
                       f"Create new configuration (n) / Change appointment date (c) / Change search criteria (s) / Quit (q)){TextColors.ENDC}: ")

        if answer.lower().strip() == 'y':
            cowinAPI.use_existing_user_config(user_config_file)
            break
        elif answer.lower().strip() == 'n':
            cowinAPI.create_new_user_config(user_config_file)
            break
        elif answer.lower().strip() == 'c':
            cowinAPI.changeAppointmentDate(user_config_file)
            break
        elif answer.lower().strip() == 's':
            cowinAPI.changeSearchCriteria(user_config_file)
            break
        elif answer.lower().strip() == 'q':
            print(f"\nExiting program...")
            exit(0)
        else:
            print(f"\n{TextColors.FAIL}Invalid input!{TextColors.ENDC}")
else:
    print("\nUser configuration file not found! Creating new user configuration...")

    cowinAPI.create_new_user_config(user_config_file)

all_centres = cowinAPI.findCentresBySearchCriteria()

if len(all_centres) == 0:
    print(f"{TextColors.FAIL}No Centre Found{TextColors.ENDC} (Either all centres are fully booked for the selected appointment date or slots aren't opened yet. "
          f"You can also try running the script again after changing date, search criteria, district or pincode)")

    while True:
        print(f"\n-->\t{TextColors.UNDERLINE}{TextColors.BOLD}Note{TextColors.ENDC}: {TextColors.WARNING}Continue with existing configuration "
              f"only if you are sure that slots are gonna open in few minutes!{TextColors.ENDC}")
        answer = input(f"\nEnter choice {TextColors.WARNING}(Continue with existing configuration (y) / "
                       f"Change appointment date (c) / Change search criteria (s)){TextColors.ENDC}: ")

        if answer.lower().strip() == 'y':
            cowinAPI.use_existing_user_config(user_config_file)
            break
        elif answer.lower().strip() == 'c':
            cowinAPI.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
            break
        elif answer.lower().strip() == 's':
            cowinAPI.changeSearchCriteria(user_config_file, load_values_from_existing_config_first=False)
            break
        else:
            print(f"\n{TextColors.FAIL}Invalid input!{TextColors.ENDC}")
else:
    centres_list = [{"Name": centre['name'], "District": centre['district_name'], "Pincode": centre['pincode'], "Vaccine Name": centre['vaccine'],
                     "Fee Type": centre['fee_type'], "Min Age": centre['min_age_limit'], "Available Capacity": centre['available_capacity'],
                     "Slots": "\n".join(centre['slots'])} for centre in all_centres]

    cowinAPI.display_table(centres_list)

    print(f"\n{TextColors.BLACKONGREY}Total Centres Found: {len(all_centres)}{TextColors.ENDC}")

while True:
    print(f"\n-->\tGetting beneficiaries registered with mobile number '{mobile}'\n")

    beneficiaries, response_statusCode = cowinAPI.get_beneficiaries()

    if response_statusCode == 200:
        break
    else:
        cowinAPI.refreshToken(user_config_file)

beneficiaries_list = [{"Ref. ID": beneficiary['beneficiary_reference_id'],
                       "Name": beneficiary['name'],
                       "Gender": beneficiary['gender'],
                       "Vaccination Status": beneficiary['vaccination_status'],
                       "Appointments": cowinAPI.get_appointment_details(beneficiary['appointments'][0]) if len(beneficiary['appointments']) > 0 else "-"}
                      for beneficiary in beneficiaries]

cowinAPI.display_table(beneficiaries_list)

print(f"\n{TextColors.BLACKONGREY}Total Beneficiaries Found: {len(beneficiaries)}{TextColors.ENDC}")

ids_input = input(f"\nEnter comma-separated index of beneficiaries to schedule appointment for {TextColors.WARNING}(Enter '0' to select all or 'q' to quit and try after sometime){TextColors.ENDC}: ")

while True:
    assert ids_input is not None and ids_input != ""

    if ids_input.strip().lower() == 'q':
        print("\nExiting program...")
        exit(0)

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
            ids_input = input(f"\nEnter comma-separated index of beneficiaries to schedule appointment for {TextColors.WARNING}(Enter '0' to select all or 'q' to quit and try after sometime){TextColors.ENDC}: ")
        else:
            break

while True:
    dose_number = input("\nEnter dose number for selected beneficiaries (SELECT ONE) ('1' for dose 1, '2' for dose 2): ")

    if dose_number is not None or dose_number.strip() != "":
        dose_number = int(dose_number)
        if dose_number in [1, 2]:
            break
        else:
            print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

while True:
    min_age_limit = input("\nEnter min age limit for selected beneficiaries (SELECT ONE) ('1' for 18+, '2' for 45+): ")

    if min_age_limit is not None or min_age_limit.strip() != "":
        min_age_limit = int(min_age_limit)
        if min_age_limit in [1, 2]:
            min_age_limit = 18 if min_age_limit == 1 else 45
            break
        else:
            print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")
    else:
        print(f"\n{TextColors.FAIL}Invalid input! Please enter one of the above two choices{TextColors.ENDC}")

print(f"\n-->\tAttempting to book appointment {TextColors.WARNING}(every 3 seconds for next 4 minutes, i.e., total 80 attempts){TextColors.ENDC}", end="")

attempts = 0

while True:
    try:
        if attempts < 80:
            print(f"\n\n{TextColors.UNDERLINE}{TextColors.BOLD}ATTEMPT {attempts+1}:{TextColors.ENDC}")
            appointment_booked_flag, appointment_id = cowinAPI.schedule_appointment(all_centres, reference_ids, dose_number, min_age_limit, user_config_file)

            if appointment_booked_flag:
                break

            attempts += 1
            time.sleep(1)

            print(f"\n\n{TextColors.WARNING}[+]{TextColors.ENDC} Updating all_centres list to refresh "
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
        exit(1)

if not appointment_booked_flag:
    print(f"\n{TextColors.FAIL}FAILED: Appointment could not be booked, as no valid slot found to be available. Please try again after 1 minute.{TextColors.ENDC}")
