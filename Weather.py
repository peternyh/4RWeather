#conda install conda-forge::google-api-python-client
#conda install google-auth-oauthlib
#conda install google-auth-httplib2
#conda install lxml
#conda install beautifulsoup4

# import the required libraries 
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
import os.path 
import base64 
import email 
from bs4 import BeautifulSoup 
import requests
import datetime
import time

  
class WeatherReport:
    
    def __init__(self, message):
        self.message = message
        self.reportDict = {}
        
        self.getEmailData()
        self.markEmailRead()
        self.getEmailPayload()
        self.getMessageBody()
        self.parseBody()
        self.transmitToWunderground()
        
    def getEmailData(self):
        self.txt = service.users().messages().get(userId='me', id=self.message['id']).execute()
        
    def markEmailRead(self):
        service.users().messages().modify(userId='me', id=self.message['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        
    def markEmailUnread(self):
        service.users().messages().modify(userId='me', id=self.message['id'], body={'addLabelIds': ['UNREAD']}).execute()
        
    def getEmailPayload(self):
        self.payload = self.txt['payload']
        self.headers = self.payload['headers']
        
    def getMessageBody(self):
        # The Body of the message is in Encrypted format. So, we have to decode it. 
        # Get the data and decode it with base 64 decoder. 
        parts = self.payload.get('parts')[0] 
        data = parts['body']['data'] 
        data = data.replace("-","+").replace("_","/") 
        decoded_data = base64.b64decode(data) 
        
        # Now, the data obtained is in lxml. So, we will parse  
        # it with BeautifulSoup library 
        soup = BeautifulSoup(decoded_data , "lxml") 
        bodies = soup.body() 
        self.body = bodies[0].get_text() #I dont understand html soup, but seems like 0 element returned from soup.body() always has what you want
        
    def parseBody(self):
        if 'DP' in self.body: #we can change this to pick whatever keyword you want to identify report messages
            items = self.body.split('\r\n')
            for ii,header in enumerate(items):
                if ii==1:
                    self.datetime = header
                    if '#' in header:
                        self.date_str = "&dateutc=now"
                        print("There was a #")
                    else:
                        self.date_str = "&dateutc=now"
                        print("There was no #")
                else:
                    temp = header.split(': ')
                    try:
                        key = temp[0]
                        value = temp[1]
                        self.reportDict[key] = value
                    except:
                        print(f'{temp} is not a valid string for parsing.')
                        
    def transmitToWunderground(self):
        # https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=KCAMOUNT479&PASSWORD=ptk9UwO3&dateutc=2024-03-03+00%3A12%3A00&tempf=34&humidity=58&dewptf=35&baromin=29.92&winddir=165&windspeedmph=9&windgustmph=12&rainin=0.123&dailyrainin=1.234&uv=1
        # https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?
        # ID=KCAMOUNT479&
        # PASSWORD=ptk9UwO3&
        # dateutc=2024-03-03+00%3A12%3A00&
        # tempf=34&
        # humidity=58&
        # dewptf=35&
        # baromin=29.92&
        # winddir=165&
        # windspeedmph=9&
        # windgustmph=12&
        # rainin=0.123&
        # dailyrainin=1.234&
        # uv=1
        # create a string to hold the first part of the URL
        WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
        WU_station_id = "KCAMOUNT479" # Replace XXXX with your PWS ID
        WU_station_pwd = "ptk9UwO3" # Replace YYYY with your Password
        WUcreds = "ID=" + WU_station_id + "&PASSWORD="+ WU_station_pwd
        
        try:
            wind = self.reportDict['W'].split(' @ ')
            winddir = wind[0]
            windspeed = wind[1].split(' / ')[0]
            windgust = wind[1].split(' / ')[1]
        except:
            print("I'm missing some wind value. This is probably a log message?")
            self.markEmailUnread()
        
        try: #this is your brute force error catching.
            BP = float(self.reportDict['BP'])+3.19
            BP = f'{BP}'
        
            r= requests.get(WUurl +
                        WUcreds +
                        self.date_str +
                        "&tempf=" + self.reportDict['T'] +
                        "&humidity=" + self.reportDict['H'] +
                        "&dewptf=" + self.reportDict['DP'] +
                        "&baromin=" + BP +
                        "&winddir=" + winddir +
                        "&windspeedmph=" + windspeed +
                        "&windgustmph=" + windgust +
                        "&rainin=" + self.reportDict['R'].split(' / ')[0] +
                        "&dailyrainin=" + self.reportDict['R'].split(' / ')[2])# +)
                        # "&uv=" + self.reportDict['UV'])
                        
            print("Received " + str(r.status_code) + " " + str(r.text))
                        
            print("\n&tempf=" + self.reportDict['T'] +
                  "\n&humidity=" + self.reportDict['H'] +
                  "\n&dewptf=" + self.reportDict['DP'] +
                  "\n&baromin=" + BP +
                  "\n&winddir=" + winddir +
                  "\n&windspeedmph=" + windspeed +
                  "\n&windgustmph=" + windgust +
                  "\n&rainin=" + self.reportDict['R'].split(' / ')[0] +
                  "\n&dailyrainin=" + self.reportDict['R'].split(' / ')[2])# +)
                  # "&uv=" + self.reportDict['UV'])
        except:
            print('youre missing something')
            self.markEmailUnread()
                            
        
        
                        
        

# Define the SCOPES. If modifying it, delete the token.pickle file. 
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify'] 
  
# Variable creds will store the user access token. 
# If no valid token found, we will create one. 
creds = None
  
# The file token.pickle contains the user access token. 
# Check if it exists 
if os.path.exists('token.pickle'): 
  
    # Read the token from the file and store it in the variable creds 
    with open('token.pickle', 'rb') as token: 
        creds = pickle.load(token) 
  
# If credentials are not available or are invalid, ask the user to log in. 
if not creds or not creds.valid: 
    if creds and creds.expired and creds.refresh_token: 
        creds.refresh(Request()) 
    else: 
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES) 
        creds = flow.run_local_server(port=0) 
  
    # Save the access token in token.pickle file for the next run 
    with open('token.pickle', 'wb') as token: 
        pickle.dump(creds, token) 
        
while(1):
    t = datetime.datetime.fromtimestamp(time.time()).strftime('%c')
    # Connect to the Gmail API 
    service = build('gmail', 'v1', credentials=creds) 
      
    # request a list of all the messages 
    result = service.users().messages().list(userId='me',q="from:(925) 367-0081 is:unread").execute() 
      
    # We can also pass maxResults to get any number of emails. Like this: 
    # result = service.users().messages().list(maxResults=200, userId='me').execute() 
    messages = result.get('messages') 
      
    if messages: 
        # reports = [WeatherReport(message) for message in messages]
        reports = WeatherReport(messages[0])
        print(f'Weather updated at {t}')
    else:
        print(f'Weather NOT updated at {t}')
    # filteredReports = [report for report in reports if hasattr(report,'datetime')] # not sure if you ened this? This should get rid of any emails that weren't a normal weather report
    
    time.sleep(15)


