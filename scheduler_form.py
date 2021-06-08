import os
import re
import sys
import time
import json
import datetime as dt
from hashlib import sha256
import PySimpleGUI as simpleGUI
from CovidVaccineChecker import CoWINAPI

simpleGUI.theme("DarkBlue")
date_now = dt.datetime.today()
pincode_pattern = re.compile("^[1-9][0-9]{5}$")
mobile_number_pattern = re.compile("^[6-9][0-9]{9}$")


def create_window(finalize=False):
    colR1C1 = [[simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_1', text_color='Red', size=(1,1)),
               simpleGUI.Text('Enter Mobile Number To Continue 🛈', font='Any 13',
                              tooltip="10-digit number starting with 6/7/8/9", size=(29, 1)),
               simpleGUI.Input(key="mobile", size=(18, 1), focus=True, enable_events=True, text_color='Black', background_color='White', disabled_readonly_background_color='Grey'),
               simpleGUI.Button('Submit', key='submit')],

               [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_2', text_color='Red', size=(1,1)),
               simpleGUI.Text('Enter OTP Received 🛈', font='Any 13',
                              tooltip="There might be some delay in receiving the OTP, please wait atleast 2 minutes after clicking 'Submit'", size=(29, 1)),
               simpleGUI.Input(key="otp", size=(18, 1), focus=False, enable_events=True, text_color='Black', background_color='White', disabled_readonly_background_color='Grey'),
               simpleGUI.Button('Validate', key='validate')],

               [simpleGUI.Frame('If User Config File Exists', font='Any 8', title_color='yellow', element_justification='center', layout=[
                  [simpleGUI.Radio('Continue with existing configuration', key='y', group_id=1, default=True),
                   simpleGUI.Radio('Create new configuration', key='n', group_id=1)],
                  [simpleGUI.Radio('Change appointment date', key='c', group_id=1),
                   simpleGUI.Radio('Change search criteria', key='s', group_id=1),
                   simpleGUI.Radio('Change slot preference', key='t', group_id=1)],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_3', text_color='Red', size=(1,1)),
                   simpleGUI.Button('Continue', key='continue')]
               ])],

               [simpleGUI.Frame('If User Config File Does Not Exist', font='Any 8', title_color='yellow', element_justification='center', layout=[
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_4', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select State', size=(22, 1)),
                   simpleGUI.Combo(key='state_name', values=[], default_value='-select-', size=(26, 1)),
                   simpleGUI.Button('Next', key='next_state_name')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_5', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select District', size=(22, 1)),
                   simpleGUI.Combo(key='district_name', values=[], default_value='-select-', size=(26, 1)),
                   simpleGUI.Button('Next', key='next_district_name')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_6', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Enter Pincode Preference(s) 🛈', tooltip='comma-separated in case of multiple', size=(22, 1)),
                   simpleGUI.Input(key='pincode_preferences', size=(28, 1), enable_events=True, text_color='Black', background_color='White', disabled_readonly_background_color='Grey'),
                   simpleGUI.Button('Next', key='next_pincode_preferences')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_7', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select Search Criteria', size=(22, 1)),
                   simpleGUI.Combo(key='search_criteria', values=['Search by Pincode', 'Search by District'],
                                   default_value='-select-', size=(26, 1)),
                   simpleGUI.Button('Next', key='next_search_criteria')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_8', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select Appointment Date', size=(22, 1)),
                   simpleGUI.In(key='appointment_date', visible=True, size=(17, 1), default_text=date_now.strftime("%d-%m-%Y"), readonly=True,
                                text_color='Black', disabled_readonly_background_color='Grey'),
                   simpleGUI.CalendarButton('Calendar', target='appointment_date', pad=((2, 0), None),
                                            default_date_m_d_y=(date_now.month, date_now.day, date_now.year), format="%d-%m-%Y", size=(8, 1)),
                   simpleGUI.Button('Next', key='next_appointment_date')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_9', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select Slot Preference', size=(22, 1)),
                   simpleGUI.Combo(key='slot_preference', values=['Select Random Slot', 'Enter Manually when a Valid Centre is Found'],
                                   default_value='-select-', size=(26, 1)),
                   simpleGUI.Button('Next', key='next_slot_preference')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_10', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Enter Centre Preference(s) 🛈', size=(22, 1),
                                  tooltip='short/full name of preferred centre(s)(comma-separated in case of multiple), CAN BE BLANK AS WELL'),
                   simpleGUI.Input(key='centre_preferences', size=(28, 1), text_color='Black', background_color='White',
                                   disabled_readonly_background_color='Grey'),
                   simpleGUI.Button('Next', key='next_centre_preferences')]
               ])],

               [simpleGUI.Frame('Booking Details', font='Any 8', title_color='yellow', element_justification='center', layout=[
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_11', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Enter Beneficiaries (Index) 🛈', size=(22, 1), tooltip="Choices: 1/2/3/4 (comma-separated in case of multiple).Enter '0' to select all"),
                   simpleGUI.Input(key='reference_ids', size=(28, 1), enable_events=True, text_color='Black', background_color='White', disabled_readonly_background_color='Grey'),
                   simpleGUI.Button('Next', key='next_reference_ids')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_12', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select Dose Number', size=(22, 1)),
                   simpleGUI.Combo(key='dose_number', values=['Dose 1', 'Dose 2'], default_value='-select-', size=(26, 1)),
                   simpleGUI.Button('Next', key='next_dose_number')],
                  [simpleGUI.Text(simpleGUI.SYMBOL_RIGHT_ARROWHEAD, key='arrow_13', text_color='Red', size=(1,1)),
                   simpleGUI.Text('Select Minimum Age Group', size=(22, 1)),
                   simpleGUI.Combo(key='min_age_limit', values=['18+ Age Group', '45+ Age Group'], default_value='-select-', size=(26, 1)),
                   simpleGUI.Button('Next', key='next_min_age_limit')]
               ])],

               [simpleGUI.Text('Made with ' + u'\u2665' + ' (https://github.com/divagicha/\nCoWIN-Vaccine-Appointment-Booking)', auto_size_text=True, font='Courier 8'),
                simpleGUI.Button('Reset Form', key='clear_values', tooltip="This will clear all the above values", size=(11, 1), button_color='Yellow'),
                simpleGUI.Exit('Exit', size=(11, 1), button_color='Yellow', pad=(10,0))]]

    colR1C2 = [[simpleGUI.Frame('Output', font='Any 8', layout=[
                  [simpleGUI.Output(size=(80, 35), key='console_output', font='Courier 10', echo_stdout_stderr=True)]
               ])]]

    layout = [[simpleGUI.Column(colR1C1, background_color='', element_justification='left', key='col1'),
               simpleGUI.Column(colR1C2, background_color='', element_justification='right', key='col2', expand_y=True)]]

    win = simpleGUI.Window('Covid Vaccination Appointment Scheduler Form', layout, auto_size_text=True, auto_size_buttons=False,
                           default_element_size=(20, 1), finalize=finalize)

    return win


def enable_element(key_to_update, update_others=False):
    if isinstance(key_to_update, str):
        for key in key_list:
            if key == key_to_update:
                window[key].update(disabled=False)
            elif update_others:
                window[key].update(disabled=True)
    elif isinstance(key_to_update, list):
        for key in key_list:
            if key in key_to_update:
                window[key].update(disabled=False)
            elif update_others:
                window[key].update(disabled=True)


def disable_element(key_to_update, update_others=False):
    if isinstance(key_to_update, str):
        for key in key_list:
            if key == key_to_update:
                window[key].update(disabled=True)
            elif update_others:
                window[key].update(disabled=False)
    elif isinstance(key_to_update, list):
        for key in key_list:
            if key in key_to_update:
                window[key].update(disabled=True)
            elif update_others:
                window[key].update(disabled=False)


def show_arrow(arrow_key, update_others=True):
    """
    :param arrow_key: arrow (denoted by keys) to show/unhide
    :type arrow_key: str or list
    :param update_others: whether to apply reverse operation on others
    :type update_others: bool
    :return: None
    """
    # to hide all the keys pass "" (empty string) in 'arrow_key' parameter
    if isinstance(arrow_key, str):
        for key in arrow_keys:
            if key == arrow_key:
                window[key].update(value=simpleGUI.SYMBOL_RIGHT_ARROWHEAD)
            elif update_others:
                window[key].update(value=" ")
    elif isinstance(arrow_key, list):
        for key in arrow_keys:
            if key in arrow_key:
                window[key].update(value=simpleGUI.SYMBOL_RIGHT_ARROWHEAD)
            elif update_others:
                window[key].update(value=" ")


def load_and_display_values(user_config_file):
    cowinAPI.use_existing_user_config(user_config_file)

    user_data = cowinAPI.get_user_data()
    window['state_name'].update(value=user_data['state_name'])
    window['district_name'].update(value=user_data['district_name'])
    pincode_preferences = ', '.join(list(map(str, user_data['pincode_preferences'])))
    window['pincode_preferences'].update(value=pincode_preferences)
    window['search_criteria'].update(value='Search by Pincode' if user_data['search_criteria'] == 1 else 'Search by District')
    window['appointment_date'].update(value=user_data['appointment_date'])
    window['slot_preference'].update(value='Select Random Slot' if user_data['slot_preference'] == 1 else 'Enter Manually when a Valid Centre is Found')
    window['centre_preferences'].update(value=', '.join(user_data['centre_preferences']) if len(user_data['centre_preferences']) > 0 else '')

    cowinAPI.displayConfigFileData(user_config_file)


def clear_values():
    window['mobile'].update(value='')
    window['otp'].update(value='')
    window['y'].update(value=True)
    window['state_name'].update(value='-select-')
    window['district_name'].update(value='-select-')
    window['pincode_preferences'].update(value='')
    window['search_criteria'].update(value='-select-')
    window['appointment_date'].update(value=date_now.strftime("%d-%m-%Y"))
    window['slot_preference'].update(value='-select-')
    window['centre_preferences'].update(value='')
    window['reference_ids'].update(value='')
    window['dose_number'].update(value='-select-')
    window['min_age_limit'].update(value='-select-')


def is_input_field_active(key):
    return window[key].TKEntry['state'] != 'readonly'


def is_appointment_date_valid():
    today = dt.datetime.today().strftime('%d-%m-%Y')

    return bool(dt.datetime.strptime(cowinAPI.appointment_date, '%d-%m-%Y') >= dt.datetime.strptime(today, '%d-%m-%Y'))


def attempt_to_schedule_appointment():
    global next_operation, attempts, all_centres
    # simpleGUI.popup("Attempting to schedule appointment (every 3 seconds for next 4 minutes, i.e., total 80 attempts)\n\nNote: keep an "
    #                 "eye on the screen when the process starts, as when a valid centre gets available you will be asked to enter CAPTCHA "
    #                 "and select TIME SLOT to book and confirm your appointment", title="Scheduling Your Appointment")
    simpleGUI.popup("Attempting to schedule appointment (every 3 seconds for next 4 minutes, i.e., total 80 attempts)\n\nNote: keep an "
                    "eye on the screen when the process starts, as when a valid centre gets available you will be asked to select a "
                    "TIME SLOT to book and confirm your appointment", title="Scheduling Your Appointment")

    all_centres = cowinAPI.findCentresBySearchCriteria()

    if len(all_centres) == 0 and next_operation != 'schedule_appointment':
        print("No Centre Found (Either all centres are fully booked for the selected appointment date or slots aren't opened yet. "
              "You can continue with the same configuration or try changing date or search criteria)")

        print("\nNote: Continue with existing configuration only if you are sure that slots are gonna open in few minutes!")
        print("\n-->\tEnter choice (Continue with existing configuration (y) / "
              "Change appointment date (c) / Change search criteria (s)): ")

        enable_element(['y', 'c', 's', 'continue'], update_others=True)
        show_arrow('arrow_3')
        window['y'].update(value=True)

        next_operation = 'schedule_appointment'
        return

        # if answer.lower().strip() == 'y':
        #     # cowinAPI.use_existing_user_config(user_config_file)
        #     print("\n[+] Continuing with existing configuration", end="")
        #     break
        # elif answer.lower().strip() == 'c':
        #     cowinAPI.changeAppointmentDate(user_config_file, load_values_from_existing_config_first=False)
        #     print("\n[+] Appointment date changed successfully", end="")
        #     break
        # elif answer.lower().strip() == 's':
        #     cowinAPI.changeSearchCriteria(user_config_file, load_values_from_existing_config_first=False)
        #     print("\n[+] Search criteria changed successfully", end="")
        #     break
        # else:
        #     print("\nInvalid input! Please enter a valid option to continue")
    else:
        next_operation = ''
        # centres_list = [{"Name": centre['name'], "District": centre['district_name'], "Pincode": centre['pincode'], "Vaccine Name": centre['vaccine'],
        #                  "Fee Type": centre['fee_type'], "Min Age": centre['min_age_limit'], "Available Capacity": centre['available_capacity'],
        #                  "Slots": "\n".join(centre['slots'])} for centre in all_centres]
        #
        # cowinAPI.display_table(centres_list)

        print(f"\nTotal Centres Found: {len(all_centres)}", end="")

    attempts = 0

    # call_schedule_appointment() is defined just to resume scheduling process if it breaks in between due to invalid token
    call_schedule_appointment()


def call_schedule_appointment():
    global attempts, refresh_token, next_operation, txnId, all_centres

    appointment_booked_flag = False

    while True:
        try:
            if attempts < 80:
                print(f"\n\nATTEMPT {attempts + 1}:")
                appointment_booked_flag, appointment_id = cowinAPI.schedule_appointment(all_centres, reference_ids,
                                                                                        dose_number, min_age_limit,
                                                                                        user_config_file, is_app_gui=True)

                if appointment_booked_flag:
                    break
                elif appointment_id and appointment_id == '<REFRESH TOKEN>':
                    print("Previous TOKEN Expired!!!")
                    print("\n-->\tGenerating OTP (There might be some delay in receiving the OTP, please wait atleast 2 minutes)")
                    refresh_token = True
                    txnId = cowinAPI.generateOTP()
                    next_operation = 'call_schedule_appointment'
                    window['otp'].update(value='')
                    window['validate'].update(text='Resend')
                    enable_element(['otp', 'validate'], update_others=True)
                    show_arrow('arrow_2')
                    return

                attempts += 1
                time.sleep(1)

                print("\n\n[+] Updating all_centres list to refresh available_capacity value for each centre before next attempt", flush=True)
                sys.stdout.flush()
                time.sleep(1)
                all_centres = cowinAPI.findCentresBySearchCriteria()
                if len(all_centres) > 0:
                    print(f"Total Centres Found: {len(all_centres)}", end="")
                else:
                    print("No Centre Found (Either all centres are fully booked for the selected appointment date or slots aren't "
                          "opened yet. You can also try running the script again after changing date, search criteria, district "
                          "or pincode)", end="")
                time.sleep(1)
            else:
                break
        except KeyboardInterrupt:
            print("\n(FAILED: Scheduling interrupted by user)")
            exit(1)

    if not appointment_booked_flag:
        print("\nour appointment could not be scheduled, as no valid slot found to be available.\n\n"
              "Please try again after 1 minute...")
        simpleGUI.popup(f"Your appointment could not be scheduled, as no valid slot found to be available.\n\n"
                        f"Please try again after 1 minute...",
                        title='Appointment Not Scheduled')
    else:
        print(f"Hurray!! Your appointment has been successfully scheduled. Following are the details:\n\n"
              f"Apt. ID: {appointment_id}\n"
              f"Centre: {cowinAPI.appointment_centre_booked}\n"
              f"Date: {cowinAPI.appointment_date}\n"
              f"Slot: {cowinAPI.appointment_slot_selected}")
        simpleGUI.popup(f"Hurray!! Your appointment has been successfully scheduled. Following are the details:\n\n"
                        f"Apt. ID: {appointment_id}\n"
                        f"Centre: {cowinAPI.appointment_centre_booked}\n"
                        f"Date: {cowinAPI.appointment_date}\n"
                        f"Slot: {cowinAPI.appointment_slot_selected}",
                        title='Appointment Successfully Booked')


if __name__ == "__main__":
    window = create_window(finalize=True)

    cowinAPI = CoWINAPI(None)
    if not os.path.exists(os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/")):
        os.makedirs(os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/"))

    # if not os.path.exists(os.path.join(cowinAPI.BASE_PROJECT_DIR, "captcha/")):
    #     os.makedirs(os.path.join(cowinAPI.BASE_PROJECT_DIR, "captcha/"))

    key_list = list(window.key_dict.keys())
    keys_to_remove = ['col1', 'col2', 'console_output', 'clear_values', 'Exit']
    arrow_keys = ['arrow_1', 'arrow_2', 'arrow_3', 'arrow_4', 'arrow_5', 'arrow_6', 'arrow_7', 'arrow_8', 'arrow_9', 'arrow_10', 'arrow_11', 'arrow_12', 'arrow_13']
    # enable_event_element_keys = ['mobile', 'otp', 'pincode_preferences', 'reference_ids']
    for key in keys_to_remove + arrow_keys:
        key_list.remove(key)

    state_dict = None
    district_dict = None
    user_config_file = None
    token = None
    refresh_token = False
    last_operation = ''
    next_operation = ''
    all_centres = None
    attempts = 0

    enable_element('mobile', update_others=True)
    show_arrow('arrow_1', update_others=True)

    while True:
        event, values = window.read()
        # print(f"Event: {event}\nValues: {json.dumps(values, indent=4)}\n")
        if event in (simpleGUI.WIN_CLOSED, 'Exit'):
            break
        elif event == 'clear_values':
            clear_values()
            last_operation = ''
            next_operation = ''
            enable_element('mobile', update_others=True)
            show_arrow('arrow_1', update_others=True)
            print('\nAppointment Scheduling Form Resetted...')

            last_operation = 'clear_values'
        elif event == 'mobile':
            if mobile_number_pattern.match(values['mobile']) and is_input_field_active('mobile'):
                enable_element('submit')
            else:
                disable_element('submit')

            last_operation = 'mobile'
        elif event == 'submit':
            # print(f"mobile: {values['mobile']}")
            cowinAPI.update_class_variable('mobile', values['mobile'])
            user_config_file = os.path.join(cowinAPI.BASE_PROJECT_DIR, "user_data/user_config_" + values['mobile'] + ".json")

            if os.path.exists(user_config_file):
                try:
                    print(f"\nUser configuration file found for '{values['mobile']}'! Listing details...\n")
                    load_and_display_values(user_config_file)
                    enable_element(['y', 'n', 'c', 's', 't', 'continue'], update_others=True)
                    show_arrow('arrow_3')
                except Exception as e:
                    simpleGUI.popup("Misconfigured Config File Error", f"User config file '{user_config_file}' exists but is misconfigured. Kindly enter the details below to create config file again", f"Error: {e}")
                    txnId = cowinAPI.generateOTP()
                    window['otp'].update(value='')
                    window['validate'].update(text='Resend')
                    enable_element(['otp', 'validate'], update_others=True)
                    show_arrow('arrow_2')
            else:
                print("\n-->\tGenerating OTP (There might be some delay in receiving the OTP, please wait atleast 2 minutes)")
                txnId = cowinAPI.generateOTP()
                window['otp'].update(value='')
                window['validate'].update(text='Resend')
                enable_element(['otp', 'validate'], update_others=True)
                show_arrow('arrow_2')

            last_operation = 'submit'
        elif event == 'otp':
            if len(values['otp'].strip()) == 0 and is_input_field_active('otp'):
                window['validate'].update(text='Resend')
                enable_element(['validate'])
            else:
                window['validate'].update(text='Validate')

                if len(values['otp'].strip()) == 6 and is_input_field_active('otp'):
                    enable_element('validate')
                else:
                    disable_element(['validate'])

            last_operation = 'otp'
        elif event == 'validate':
            disable_element(['otp', 'validate'])
            if len(values['otp']) == 0:
                txnId_new = cowinAPI.generateOTP()
                if txnId_new == txnId:
                    print("[+] Last generated OTP still valid! New OTP will be generated only after expiration time of 3 mins.")
                txnId = txnId_new
                window['otp'].update(value='')
                window['validate'].update(text='Resend')
                enable_element(['otp', 'validate'], update_others=True)
                show_arrow('arrow_2')
            else:
                hashed_otp = sha256(values['otp'].encode("utf-8")).hexdigest()
                token = cowinAPI.confirmOTP(hashed_otp, txnId)
                if token:
                    if refresh_token and os.path.exists(user_config_file):
                        cowinAPI.update_class_variable('token', token, update_user_config=True, user_config_file=user_config_file)
                        refresh_token = False
                    else:
                        cowinAPI.update_class_variable('token', token)

                    if next_operation == 'next_state_name':
                        district_dict = cowinAPI.get_districtDict(state_id)
                        print("(SELECT DISTRICT FROM DROPDOWN)")
                        districts = list(district_dict.keys())
                        districts.sort()
                        window['district_name'].update(values=districts, set_to_index=0, size=(26, 8))
                        enable_element(['district_name', 'next_district_name'], update_others=True)
                        show_arrow('arrow_5')
                        next_operation = ''
                    elif next_operation == 'next_centre_preferences':
                        enable_element(['centre_preferences', 'next_centre_preferences'], update_others=True)
                        show_arrow('arrow_10')
                        next_operation = ''
                    elif next_operation == 'call_schedule_appointment':
                        enable_element('', update_others=True)
                        show_arrow('')
                        next_operation = ''
                        call_schedule_appointment()
                    elif next_operation == 'continue':
                        enable_element(['y', 'n', 'c', 's', 't', 'continue'], update_others=True)
                        show_arrow('arrow_3')
                        window['y'].update(value=True)
                    else:
                        state_dict = cowinAPI.get_stateDict()
                        print("(SELECT STATE FROM DROPDOWN)")
                        states = list(state_dict.keys())
                        states.sort()
                        window['state_name'].update(values=states, set_to_index=0, size=(26, 10))
                        enable_element(['state_name', 'next_state_name'], update_others=True)
                        show_arrow('arrow_4')
                else:
                    # Incorrect OTP Entrered!
                    enable_element('otp')

            last_operation = 'validate'
        elif event == 'continue':
            if not values['y']:
                disable_element(['y', 'n', 'c', 's', 't', 'continue'])

            if values['y']:
                if not is_appointment_date_valid():
                    simpleGUI.popup("Kindly choose 'Change appointment date' option and select a valid date "
                                    "(can be today's date or of the future)", title="Invalid Appointment Date")
                    continue

                disable_element(['y', 'n', 'c', 's', 't', 'continue'])

                if next_operation == 'schedule_appointment':
                    enable_element('', update_others=True)
                    show_arrow('')
                    attempt_to_schedule_appointment()
                elif next_operation == 'change_date_and_schedule_appointment':
                    next_operation = ''
                    enable_element('', update_others=True)
                    show_arrow('')
                    attempt_to_schedule_appointment()
                else:
                    print(f"\n-->\tGetting beneficiaries registered with mobile number '{values['mobile']}'\n")
                    beneficiaries, response_statusCode = cowinAPI.get_beneficiaries()
                    if response_statusCode == 200:
                        if not beneficiaries or len(beneficiaries) == 0:
                            simpleGUI.popup("No beneficiaries have been added in this account!",
                                            "Kindly add one or more (max. 4) beneficiaries first "
                                            "by going to link https://selfregistration.cowin.gov.in/ and then run the script again.")
                            exit(1)
                        current_year = dt.datetime.today().year
                        hidden_chars = '*' * 5
                        beneficiaries_list = [{"Ref. ID": hidden_chars+beneficiary['beneficiary_reference_id'][-4:],
                                               "Name": beneficiary['name'].split(" ")[0],
                                               "Gender": beneficiary['gender'],
                                               "Age": current_year - int(beneficiary['birth_year']),
                                               "Vaccination Status": cowinAPI.get_vaccination_status_details(
                                                   beneficiary['vaccination_status'],
                                                   beneficiary['dose1_date'],
                                                   beneficiary['dose2_date']),
                                               # "Appointment Details (Dose 1)": cowinAPI.get_appointment_details(
                                               #     beneficiary['appointments'][0]) if len(
                                               #     beneficiary['appointments']) > 0 else "-",
                                               # "Appointment Details (Dose 2)": cowinAPI.get_appointment_details(
                                               #     beneficiary['appointments'][1]) if len(
                                               #     beneficiary['appointments']) > 1 else "-"
                                               }
                                              for beneficiary in beneficiaries]

                        cowinAPI.display_table(beneficiaries_list)
                        enable_element('reference_ids', update_others=True)
                        show_arrow('arrow_11')
                    else:
                        print("Previous TOKEN Expired!!!")
                        print("\n-->\tGenerating OTP (There might be some delay in receiving the OTP, please wait atleast 2 minutes)")
                        refresh_token = True
                        txnId = cowinAPI.generateOTP()
                        next_operation = 'continue'
                        window['otp'].update(value='')
                        window['validate'].update(text='Resend')
                        enable_element(['otp', 'validate'], update_others=True)
                        show_arrow('arrow_2')

                last_operation = 'y'
            elif values['n']:
                try:
                    state_dict = cowinAPI.get_stateDict()
                    print("(SELECT STATE FROM DROPDOWN)")
                    states = list(state_dict.keys())
                    states.sort()
                    window['state_name'].update(values=states, set_to_index=0, size=(26, 10))
                    enable_element(['state_name', 'next_state_name'], update_others=True)
                    show_arrow('arrow_4')
                except Exception as e:
                    print("Previous TOKEN Expired!!!")
                    print("\n-->\tGenerating OTP (There might be some delay in receiving the OTP, please wait atleast 2 minutes)")
                    refresh_token = True
                    txnId = cowinAPI.generateOTP()
                    window['otp'].update(value='')
                    window['validate'].update(text='Resend')
                    enable_element(['otp', 'validate'], update_others=True)
                    show_arrow('arrow_2')

                last_operation = 'n'
            elif values['c']:
                enable_element(['Calendar', 'next_appointment_date'], update_others=True)
                show_arrow('arrow_8')

                last_operation = 'c'
            elif values['s']:
                enable_element(['search_criteria', 'next_search_criteria'], update_others=True)
                show_arrow('arrow_7')

                last_operation = 's'
            elif values['t']:
                enable_element(['slot_preference', 'next_slot_preference'], update_others=True)
                show_arrow('arrow_9')

                last_operation = 't'
        elif event == 'next_state_name':
            disable_element(['state_name', 'next_state_name'])
            state_id = state_dict[values['state_name']]
            cowinAPI.update_class_variable('state_id', state_id)
            cowinAPI.update_class_variable('state_name', values['state_name'])
            try:
                district_dict = cowinAPI.get_districtDict(state_id)
                print("(SELECT DISTRICT FROM DROPDOWN)")
                districts = list(district_dict.keys())
                districts.sort()
                window['district_name'].update(values=districts, set_to_index=0, size=(26, 8))
                enable_element(['district_name', 'next_district_name'], update_others=True)
                show_arrow('arrow_5')
            except Exception as e:
                print("Previous TOKEN Expired!!!")
                print("\n-->\tGenerating OTP (There might be some delay in receiving the OTP, please wait atleast 2 minutes)")
                refresh_token = True
                txnId = cowinAPI.generateOTP()
                next_operation = 'next_state_name'
                window['otp'].update(value='')
                window['validate'].update(text='Resend')
                enable_element(['otp', 'validate'], update_others=True)
                show_arrow('arrow_2')

            last_operation = 'next_state_name'
        elif event == 'next_district_name':
            disable_element(['district_name', 'next_district_name'])
            district_id = district_dict[values['district_name']]
            cowinAPI.update_class_variable('district_id', district_id)
            cowinAPI.update_class_variable('district_name', values['district_name'])
            enable_element('pincode_preferences')
            show_arrow('arrow_6')

            if values['pincode_preferences'].strip() != "" and is_input_field_active('pincode_preferences'):
                pincode_list = values['pincode_preferences'].strip().replace(" ", "").split(",")
                areValidPincodes = [bool(pincode_pattern.match(pincode)) for pincode in pincode_list if pincode != '']
                if False not in areValidPincodes:
                    pincode_preferences = [int(pincode) for pincode in pincode_list if pincode != '']
                    enable_element('next_pincode_preferences')

            last_operation = 'next_district_name'
        elif event == 'pincode_preferences':
            if values['pincode_preferences'].strip() != "" and is_input_field_active('pincode_preferences'):
                pincode_list = values['pincode_preferences'].strip().replace(" ", "").split(",")
                areValidPincodes = [bool(pincode_pattern.match(pincode)) for pincode in pincode_list if pincode != '']
                if False not in areValidPincodes:
                    pincode_preferences = [int(pincode) for pincode in pincode_list if pincode != '']
                    enable_element('next_pincode_preferences')
                else:
                    disable_element('next_pincode_preferences')
            else:
                disable_element('next_pincode_preferences')

            last_operation = 'pincode_preferences'
        elif event == 'next_pincode_preferences':
            disable_element(['pincode_preferences', 'next_pincode_preferences'])
            cowinAPI.update_class_variable('pincode_preferences', pincode_preferences)
            enable_element(['search_criteria', 'next_search_criteria'], update_others=True)
            show_arrow('arrow_7')

            last_operation = 'next_pincode_preferences'
        elif event == 'next_search_criteria':
            if values['search_criteria'] != '-select-':
                if last_operation == 's':
                    cowinAPI.update_class_variable('search_criteria', 1 if values['search_criteria'] == 'Search by Pincode' else 2, update_user_config=True, user_config_file=user_config_file)
                else:
                    cowinAPI.update_class_variable('search_criteria', 1 if values['search_criteria'] == 'Search by Pincode' else 2)

                if next_operation == 'schedule_appointment':
                    enable_element(['y', 'c', 's', 'continue'], update_others=True)
                    show_arrow('arrow_3')
                    window['y'].update(value=True)
                elif last_operation == 's':
                    enable_element(['y', 'n', 'c', 's', 't', 'continue'], update_others=True)
                    show_arrow('arrow_3')
                    window['y'].update(value=True)
                else:
                    enable_element(['Calendar', 'next_appointment_date'], update_others=True)
                    show_arrow('arrow_8')

            last_operation = 'next_search_criteria'
        elif event == 'next_appointment_date':
            if last_operation == 'c':
                cowinAPI.update_class_variable('appointment_date', values['appointment_date'], update_user_config=True, user_config_file=user_config_file)
            else:
                cowinAPI.update_class_variable('appointment_date', values['appointment_date'])

            if next_operation == 'schedule_appointment':
                enable_element(['y', 'c', 's', 'continue'], update_others=True)
                show_arrow('arrow_3')
                window['y'].update(value=True)
                # enable_element('', update_others=True)
                # show_arrow('')
                # attempt_to_schedule_appointment()
            elif next_operation == 'change_date_and_schedule_appointment':
                enable_element(['y', 'c', 'continue'], update_others=True)
                show_arrow('arrow_3')
                window['y'].update(value=True)
            elif last_operation == 'c':
                enable_element(['y', 'n', 'c', 's', 't', 'continue'], update_others=True)
                show_arrow('arrow_3')
                window['y'].update(value=True)
            else:
                enable_element(['slot_preference', 'next_slot_preference'], update_others=True)
                show_arrow('arrow_9')

            last_operation = 'next_appointment_date'
        elif event == 'next_slot_preference':
            if values['slot_preference'] != '-select-':
                if last_operation == 't':
                    cowinAPI.update_class_variable('slot_preference', 1 if values['slot_preference'] == 'Select Random Slot' else 2, update_user_config=True, user_config_file=user_config_file)
                else:
                    cowinAPI.update_class_variable('slot_preference', 1 if values['slot_preference'] == 'Select Random Slot' else 2)

                if next_operation == 'schedule_appointment':
                    enable_element('', update_others=True)
                    show_arrow('')
                    attempt_to_schedule_appointment()
                elif last_operation == 't':
                    enable_element(['y', 'n', 'c', 's', 't', 'continue'], update_others=True)
                    show_arrow('arrow_3')
                    window['y'].update(value=True)
                else:
                    enable_element(['centre_preferences', 'next_centre_preferences'], update_others=True)
                    show_arrow('arrow_10')

            last_operation = 'next_slot_preference'
        elif event == 'next_centre_preferences':
            if values['centre_preferences'].strip() != '':
                centre_preferences = values['centre_preferences'].strip().replace(", ", ",").replace(" ,", ",").lower().split(",")
                cowinAPI.update_class_variable('centre_preferences', [centre for centre in centre_preferences if centre != ''])
            else:
                centre_preferences = []
                cowinAPI.update_class_variable('centre_preferences', centre_preferences)

            cowinAPI.save_user_config(user_config_file)
            print(f"\n-->\tGetting beneficiaries registered with mobile number '{values['mobile']}'\n")
            beneficiaries, response_statusCode = cowinAPI.get_beneficiaries()
            if response_statusCode == 200:
                if not beneficiaries or len(beneficiaries) == 0:
                    simpleGUI.popup("No beneficiaries have been added in this account!",
                                    "Kindly add one or more (max. 4) beneficiaries first "
                                    "by going to link https://selfregistration.cowin.gov.in/ and then run the script again.")
                    exit(1)
                current_year = dt.datetime.today().year
                hidden_chars = '*' * 5
                beneficiaries_list = [{"Ref. ID": hidden_chars+beneficiary['beneficiary_reference_id'][-4:],
                                       "Name": beneficiary['name'].split(" ")[0],
                                       "Gender": beneficiary['gender'],
                                       "Age": current_year - int(beneficiary['birth_year']),
                                       "Vaccination Status": cowinAPI.get_vaccination_status_details(
                                           beneficiary['vaccination_status'],
                                           beneficiary['dose1_date'],
                                           beneficiary['dose2_date']),
                                       # "Appointment Details (Dose 1)": cowinAPI.get_appointment_details(
                                       #     beneficiary['appointments'][0]) if len(
                                       #     beneficiary['appointments']) > 0 else "-",
                                       # "Appointment Details (Dose 2)": cowinAPI.get_appointment_details(
                                       #     beneficiary['appointments'][1]) if len(
                                       #     beneficiary['appointments']) > 1 else "-"
                                       }
                                      for beneficiary in beneficiaries]

                cowinAPI.display_table(beneficiaries_list)
                enable_element('reference_ids', update_others=True)
                show_arrow('arrow_11')
            else:
                print("Previous TOKEN Expired!!!")
                print("\n-->\tGenerating OTP (There might be some delay in receiving the OTP, please wait atleast 2 minutes)")
                refresh_token = True
                txnId = cowinAPI.generateOTP()
                next_operation = 'next_centre_preferences'
                window['otp'].update(value='')
                window['validate'].update(text='Resend')
                enable_element(['otp', 'validate'], update_others=True)
                show_arrow('arrow_2')

            last_operation = 'next_centre_preferences'
        elif event == 'reference_ids':
            if values['reference_ids'].strip() != "" and is_input_field_active('reference_ids'):
                reference_ids = values['reference_ids'].strip().replace(" ", "").split(",")
                # print(f"reference_ids: {reference_ids}")
                try:
                    areValidIndexes = [bool(0 <= int(index) <= len(beneficiaries)) for index in reference_ids if index != '']
                    if False not in areValidIndexes:
                        reference_ids = [int(index) for index in reference_ids if index != '']
                        enable_element('next_reference_ids')
                    else:
                        disable_element('next_reference_ids')
                except Exception as e:
                    print("\nInvalid character found!! Enter only comma-separated numbers")
                    disable_element('next_reference_ids')
            else:
                disable_element('next_reference_ids')

            last_operation = 'reference_ids'
        elif event == 'next_reference_ids':
            if reference_ids[0] == 0:
                reference_ids = [beneficiary['beneficiary_reference_id'] for beneficiary in beneficiaries]
            else:
                reference_ids = [beneficiaries[index-1]['beneficiary_reference_id'] for index in reference_ids if 0 < index <= len(beneficiaries)]
            enable_element(['dose_number', 'next_dose_number'], update_others=True)
            show_arrow('arrow_12')

            last_operation = 'next_reference_ids'
        elif event == 'next_dose_number':
            if values['dose_number'] != '-select-':
                dose_number = 1 if values['dose_number'] == 'Dose 1' else 2
                enable_element(['min_age_limit', 'next_min_age_limit'], update_others=True)
                show_arrow('arrow_13')

            last_operation = 'next_dose_number'
        elif event == 'next_min_age_limit':
            if values['min_age_limit'] != '-select-':
                min_age_limit = 18 if values['min_age_limit'] == '18+ Age Group' else 45
                disable_element(['min_age_limit', 'next_min_age_limit'])

                if is_appointment_date_valid():
                    show_arrow('')
                    attempt_to_schedule_appointment()
                else:
                    simpleGUI.popup("Kindly choose 'Change appointment date' option and select a valid date "
                                    "(can be today's date or of the future)", title="Invalid Appointment Date")
                    enable_element(['y', 'c', 'continue'], update_others=True)
                    show_arrow('arrow_3')
                    window['c'].update(value=True)
                    next_operation = 'change_date_and_schedule_appointment'

            last_operation = 'next_min_age_limit'

    window.close()
