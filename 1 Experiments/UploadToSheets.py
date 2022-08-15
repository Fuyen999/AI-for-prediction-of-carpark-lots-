#Run this code every night to scrape data, leave it running for the whole day
#Pandas, Json and formatting stuff
import pandas as pd
import requests
import json
from datetime import datetime

#GSheets Stuff
import gspread
from df2gspread import df2gspread as d2g
from df2gspread import gspread2df as g2d
from oauth2client.service_account import ServiceAccountCredentials

#For Sleep
import time

# looks for empty row based on values appearing in 1st N columns
def next_available_row(sheet, cols_to_sample=2):
    try:
        cols = sheet.range(1, 1, sheet.row_count, cols_to_sample)
        return max([cell.row for cell in cols if cell.value]) + 1
    except:
        return 1
    
#Set start and end time here
start_hour = "12"
end_hour = "00"

#Start automatically at start_hour (please run the code before sleep every night)
while (datetime.now().strftime("%H") != start_hour):
    print(datetime.now().strftime("%H:%M:%S"),end="\r")
    time.sleep(1)
    
#Credential stuff
scope = ["https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("./creds.json", scope)
gc = gspread.authorize(credentials)

#Get spreadsheet key (please open spreadsheet and add key into spreadsheet.txt beforehand)
key_to_spreadsheet_key = "1bms8J3Hiv_F3Mycsr14gwVZiJi1-ngLj0fNhdRkIAwQ"
wks_name = 'Sheet1'
df = g2d.download(key_to_spreadsheet_key, wks_name, col_names=False, row_names=False, credentials=credentials, start_cell='A1')
spreadsheet_key = list(df[1][df[0] == datetime.now().strftime("%d/%m")])[0]

print("This script will grab data from LTA and upload it to "
      "https://docs.google.com/spreadsheets/d/"+spreadsheet_key+"/edit#gid=0 every 10 min. ")
print("Press Ctrl + C to stop.\n")

#API URL (Total data per set = 2338)
url_list = []
headers = {'AccountKey': 'opoOfz6bTza7BMCTCy8VFA=='}
for skip in range(0,2500,500):
    url_list.append('http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2?$skip='+str(skip))

#End automatically at end_hour
while (datetime.now().strftime("%H") != end_hour):
    df = pd.DataFrame(columns=['CarParkID','Area','Development','Location','AvailableLots','LotType','Agency'])
    for url in url_list:
        response = requests.get(url, headers=headers)
        carpark_info = json.loads(response.text)
        df = df.append(pd.DataFrame(carpark_info['value']), ignore_index=True)
        
    #df = pd.DataFrame(df[["CarParkID","AvailableLots"]])
        
    #Insert date and time into dataframe
    now = datetime.now()
    d_string = now.strftime("%d/%m/%Y")
    df.insert(0,'Date',d_string)
    t_string = now.strftime("%H:%M:%S")
    df.insert(0,'Time',t_string)
    print("Extracted data for "+d_string+" "+t_string)
        
    row = next_available_row(gc.open_by_key(spreadsheet_key).worksheet(wks_name),1)
    d2g.upload(df, spreadsheet_key, wks_name, col_names=False, row_names=False, clean=False, credentials=credentials, start_cell='A{}'.format(row))
    print("Upload succeeded. Sleeping for 10 min.")

    for i in range(1,600):
        print(str(int(i/60))+" minutes "+str(i%60)+" seconds elapsed",end="\r")
        time.sleep(1)

    print("\n")