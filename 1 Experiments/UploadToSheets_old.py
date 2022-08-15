#Pandas, Json and formatting stuff
import pandas as pd
import requests
import json
from datetime import datetime
#GSheets Stuff
import gspread
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials
#For Sleep
import time

print("This script will grab data from LTA and upload it to "
      "https://docs.google.com/spreadsheets/d/1l23_ZsTsHwzUms_gmx5JZ6ii06WGR93YiXW8vdwBXAs/edit#gid=0 every min. ")
print("Press Ctrl + C to stop.")

while True:
    print("Extracting data from LTA.")
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2'
    headers = {'AccountKey': 'opoOfz6bTza7BMCTCy8VFA=='}
    response = requests.get(url, headers=headers)
    carpark_info = json.loads(response.text)
    df = pd.DataFrame(carpark_info['value'])
    now = datetime.now()
    d_string = now.strftime("%d/%m/%Y")
    df.insert(0,'Date',d_string)
    t_string = now.strftime("%H:%M:%S")
    df.insert(0,'Time',t_string)
    print("Extracted data for "+d_string+" "+t_string)

    def next_available_row(sheet, cols_to_sample=2):
      # looks for empty row based on values appearing in 1st N columns
        try:
            cols = sheet.range(1, 1, sheet.row_count, cols_to_sample)
            return max([cell.row for cell in cols if cell.value]) + 1
        except:
            return 1
    scope = ["https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("./creds.json", scope)
    gc = gspread.authorize(credentials)
    spreadsheet_key = '1l23_ZsTsHwzUms_gmx5JZ6ii06WGR93YiXW8vdwBXAs'
    wks_name = 'Sheet1'
    row = next_available_row(gc.open_by_key(spreadsheet_key).worksheet(wks_name),1)
    print("Uploading data to google sheets.")
    d2g.upload(df, spreadsheet_key, wks_name, col_names=False, row_names=False, clean=False, credentials=credentials, start_cell='A{}'.format(row))
    print("Uploading succeeded. Sleeping for 1 min.")

    for i in range(1,61):
        print(str(i)+" seconds elapsed.",end="\r")
        time.sleep(1)

    print("Running again.")


