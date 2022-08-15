# Pandas, Json and formatting stuff
import pandas as pd
import requests
import json
from datetime import datetime

# GSheets Stuff
import gspread
from df2gspread import df2gspread as d2g
from df2gspread import gspread2df as g2d
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery

# For Sleep
import time

# looks for empty row based on values appearing in 1st N columns
def next_available_row(sheet, cols_to_sample=2):
    try:
        cols = sheet.range(1, 1, sheet.row_count, cols_to_sample)
        return max([cell.row for cell in cols if cell.value]) + 1
    except:
        return 1


def upload_to_sheets():
    # Run this code every night to scrape data, leave it running for the whole day
    # Credential stuff
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("./creds.json", scope)
    gc = gspread.authorize(credentials)

    # Set start and end time here
    start_hour = "06"
    end_hour = "00"
    print("Data Collection will start at "+start_hour+" 00 HR.")

    # Start automatically at start_hour (please run the code before sleep every night)
    while (datetime.now().strftime("%H") != start_hour):
        print(datetime.now().strftime("%H:%M:%S"), end="\r")
        time.sleep(1)

    # Name new google sheets with in this format: <today's date>_carpark_availability
    wks_name = 'Sheet1'
    newsheet_name = "{}/{}/{}_carpark_availability".format(int(datetime.now().strftime("%d")),
                                                           int(datetime.now().strftime("%m")),
                                                           int(datetime.now().strftime("%Y")))
    destFolderId = "15ZD6Jp7ZeWJLOSm2CxmMzSjJ6fqtLfR_"
    drive_service = discovery.build('drive', 'v3', credentials=credentials)

    # Check if a sheet is already created for the day
    file_list = drive_service.files().list(q="name contains '{}'".format(newsheet_name),
                                           spaces='drive',
                                           fields='nextPageToken, files(id, name)',
                                           pageToken=None).execute()
    file_list = file_list.get("files", [])

    # to delete a file (debug purpose)
    # for file in file_list:
    #    drive_service.files().delete(fileId=file['id']).execute()

    # Create sheet
    if (file_list == []):
        body = {'name': newsheet_name,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': [destFolderId]}
        newsheet = drive_service.files().create(body=body).execute()
        spreadsheet_key = newsheet['id']
        new_sheet = gc.open_by_key(spreadsheet_key).worksheet(wks_name)
        new_sheet.delete_columns(1, 18)

        # Update sheet's link to the google sheet that stores all spreadsheet keys
        spreadsheet_key_sheet = gc.open_by_key("1bms8J3Hiv_F3Mycsr14gwVZiJi1-ngLj0fNhdRkIAwQ").worksheet(wks_name)
        row = next_available_row(spreadsheet_key_sheet, 1)
        spreadsheet_key_sheet.update("A{}".format(row),
                                     "{}/{}".format(datetime.now().strftime("%d"), datetime.now().strftime("%m")))
        spreadsheet_key_sheet.update("B{}".format(row), spreadsheet_key)
        spreadsheet_key_sheet.update("F{}".format(row),
                                     "https://docs.google.com/spreadsheets/d/{}/edit#gid=0".format(spreadsheet_key))
    else:
        spreadsheet_key = file_list[0]['id']

    # old code
    # df = g2d.download(key_to_spreadsheet_key, wks_name, col_names=False, row_names=False, credentials=credentials, start_cell='A1')
    # spreadsheet_key = list(df[1][df[0] == datetime.now().strftime("%d/%m")])[0]

    print("This script will grab data from LTA and upload it to "
          "https://docs.google.com/spreadsheets/d/" + spreadsheet_key + "/edit#gid=0 every 10 min. ")
    print("Press Ctrl + C to stop.\n")

    # LTA API URL (Total data per set = 2338)
    url_list = []
    headers = {'AccountKey': 'opoOfz6bTza7BMCTCy8VFA=='}
    for skip in range(0, 2500, 500):
        url_list.append('http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2?$skip=' + str(skip))

    # End automatically at end_hour
    while (datetime.now().strftime("%H") != end_hour):
        df = pd.DataFrame(
            columns=['CarParkID', 'Area', 'Development', 'Location', 'AvailableLots', 'LotType', 'Agency'])
        for url in url_list:
            response = requests.get(url, headers=headers)
            carpark_info = json.loads(response.text)
            df = df.append(pd.DataFrame(carpark_info['value']), ignore_index=True)

        # df = pd.DataFrame(df[["CarParkID","AvailableLots"]])

        # Insert date and time into dataframe
        now = datetime.now()
        d_string = now.strftime("%d/%m/%Y")
        df.insert(0, 'Date', d_string)
        t_string = now.strftime("%H:%M:%S")
        df.insert(0, 'Time', t_string)
        print("Extracted data for " + d_string + " " + t_string)

        # Upload to sheets
        row = next_available_row(gc.open_by_key(spreadsheet_key).worksheet(wks_name), 1)
        d2g.upload(df, spreadsheet_key, wks_name, col_names=False, row_names=False, clean=False,
                   credentials=credentials, start_cell='A{}'.format(row))
        print("Upload succeeded. Sleeping for 10 min.")

        # Sleep for 10 minutes
        for i in range(1, 600):
            print(str(int(i / 60)) + " minutes " + str(i % 60) + " seconds elapsed", end="\r")
            time.sleep(1)

        print("\n")

        
upload_to_sheets()