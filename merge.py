import json
from pymongo import MongoClient
import re
from datetime import datetime,timezone
import time
from webbot import Browser
from flask import Flask, request,jsonify
from pymongo import MongoClient 

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017')
db = client.CargoTracking


# Function to pause execution for 'n' seconds
def wait(n):
    time.sleep(n)

# Function to remove spaces and pipe characters from a string
def removeSpaces(x, all_spaces=False):
    # If 'all_spaces' is True, remove all spaces in the string
    if all_spaces:
        x = x.replace(' ', '')

    # Remove spaces at the beginning of the string
    x = re.sub(r'^\s+', '', x)

    # Remove spaces at the end of the string
    x = re.sub(r'\s+$', '', x)

    # Remove '|' character
    x = x.replace('|', '')

    # Replace multiple consecutive spaces with a single space
    x = re.sub(r'\s{2,}', ' ', x)

    # Return the modified string
    return x

# Define a route for scraping and storing data

def tracking():
    id = request.args.get('number')
    
    if '-' in id:
        # Split the id by hyphen and keep only the part after the hyphen
        id_parts = id.split('-')
        id = id_parts[-1]   
         # Construct a response dictionary
    response = {
        'id': id,
        'status': 'loading',
        'message': "wait for some time Thank You"
    }
    return response


def scrape_Qatar_cargo(track_id,air_code):
    airline_code = air_code
    date = datetime.now().strftime('%m-%d-%Y')
    tracking_id_complete=track_id
    tracking_id=track_id
    id_parts = tracking_id.split('-')
    tracking_id= id_parts[-1]   
    # Connect to the MongoDB
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC

    # # Check if data already exists in MongoDB
    data_in_mongo = collection.find_one({'complete_number': tracking_id_complete, 'airline_code': air_code,'date':date})
    if data_in_mongo is not None:
        # Check if the data in MongoDB is from today's date
        today = datetime.now().date()
        mongo_date = data_in_mongo.get('date', None)
        # Data from today's date, return it
        milestone = data_in_mongo.get('milestone', [])
        flight_detail = data_in_mongo.get('flight_detail', [])
        truck_detail = data_in_mongo.get('truck_detail', [])

        return {
            "message": "Data loaded from MongoDB",
            "milestone": milestone,
            "flight_detail": flight_detail,
            "truck_detail": truck_detail
        }
    else:
        # Data doesn't exist in MongoDB, scrape and store it
        web = Browser()
        # ... (The scraping part of your code, same as before)
        web.driver.get("https://www.qrcargo.com/s/track-your-shipment")
        web.driver.maximize_window()
        wait(2)
    # Find and interact with HTML elements
    textbox = web.driver.find_element_by_xpath('//div[@class="staticlabel"]')
    wait(2)

            
    input = web.driver.find_element_by_xpath('//input[@data-id="docawb"]')
    input.send_keys(tracking_id)
    wait(2)
    textbox = web.driver.find_element_by_xpath('//button[@class="slds-button slds-button_brand slds-button_stretch small-btn small-btn-pad"]')
    textbox.click()
    wait(2)
    # Format for converting the date and time to a string
    out_form = '%Y-%m-%d %H:%M:%S'
    # Format for parsing the date and time from a string
    in_form = '%A-%d-%b-%Y %H:%M'

    # Extract milestones from the web page
    milestones = web.driver.find_elements_by_xpath('//div[@class="slds-col slds-size_1-of-1 slds-medium-size_12-of-12 slds-large-size_6-of-12 qrds-cargo-track-details-ipad"]/ul')
    wait(2)

# Process and clean up the extracted data
    milestone = []
    for i in range(0, len(milestones)):
            status = milestones[i].find_element_by_xpath("li[2]/ul/li[1]").text
            pieces_weight = milestones[i].find_element_by_xpath("li[2]/ul/li[2]").text
            day_date_month_year = milestones[i].find_element_by_xpath("li[3]/ul/li[1]").text
            time = milestones[i].find_element_by_xpath("li[3]/ul/li[2]").text

            # Call the removeSpaces function to clean up the extracted data
            status = removeSpaces(status)
            pieces_weight = removeSpaces(pieces_weight)
            day_date_month_year = removeSpaces(day_date_month_year)
            time = removeSpaces(time)

            data1 = {"status": status, "pieces_weight": pieces_weight, "day_date_month_year": day_date_month_year, "time": time}
            milestone.append(data1)
    start = 0
    truck_detail = []
    # Check if a specific image URL exists in the web page source
    if '/resource/1697029428000/QCG_assets/icons/truck_blackdot.svg' in web.get_page_source():
        # If the image URL is found, set 'start' to 3
        start = 3
        fromm = web.driver.find_element_by_xpath('//*[local-name()="text"][1]').text
        to = web.driver.find_element_by_xpath('//*[local-name()="text"][4]').text
        truck_id=web.driver.find_element_by_xpath('//*[local-name()="text"][2]').text

        data4 = {"from": fromm, "TO": to,"truck_info":truck_id}
        truck_detail.append(data4)

        
    # Process and clean up the second set of data
    flight_detail = []
    for i in range(start, 100, 5):
        try:
            fromm = web.driver.find_element_by_xpath('//*[local-name()="text"][' + str(i + 1) + ']').text
            flight_number = web.driver.find_element_by_xpath('//*[local-name()="text"][' + str(i + 2) + ']').text
            departure_date_time = web.driver.find_element_by_xpath('//*[local-name()="text"][' + str(i + 3) + ']').text
            arrival_date_time = web.driver.find_element_by_xpath('//*[local-name()="text"][' + str(i + 4) + ']').text
            to = web.driver.find_element_by_xpath('//*[local-name()="text"][' + str(i + 6) + ']').text

            data3 = {"from": fromm, "TO": to, "flight_number": flight_number, "departure_date_time": departure_date_time, "arrival_date_time": arrival_date_time}
            flight_detail.append(data3)
        except Exception as e:
            break
    if len(milestone )==0 and len(flight_detail)==0:
        return{"message":"no data found or wrong number"}        
        
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC
    collection.insert_one({"milestone": milestone, "flight_detail": flight_detail,"truck_detail": truck_detail,'complete_number':tracking_id_complete,'airline_code':air_code,'date':date})
    # # Return a JSON response with the scraped data
    return {"message": "Data Loading", "milestone": milestone, "flight_detail": flight_detail,"truck_detail": truck_detail}


def scrape_Emirates_cargo(track_id,air_code):
    # get trcking id from request
    tracking_id_complete = track_id
    tracking_id = track_id
    tracking_id = tracking_id.replace('-', '')
    date = datetime.now().strftime('%m-%d-%Y')
    airline_code=air_code
   
      # Connect to the MongoDB
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC

    # Check if data already exists in MongoDB
    data_in_mongo = collection.find_one({'complete_number':tracking_id_complete,'airline_code':airline_code,'date':date})  # Find one document, you can add specific query criteria


    if data_in_mongo is not None:
        # Check if the data in MongoDB is from today's date
        today = datetime.now().date()
        mongo_date = data_in_mongo.get('date', None)

    
        # Data from today's date, return it
        milestones = data_in_mongo.get('milestones', [])
        flight_detail = data_in_mongo.get('flight_detail', [])
        # truck_detail = data_in_mongo.get('truck_detail', [])

        return {
            "message": "Data loaded from MongoDB",
            "milestones": milestones,
            "flight_detail": flight_detail,
        }
       
    else:   
            web = Browser()
            web.driver.get("https://eskycargo.emirates.com/app/offerandorder/#/home/find-offer")
            web.driver.maximize_window()
            wait(1)
            while(True):
                try:
                    web.driver.find_element_by_xpath( '//input[@placeholder="Doc. No. e.g.: 17602268011"]').send_keys(tracking_id)
                    break
                except:
                    time.sleep(1)
                    continue
            wait(1)
            web.driver.find_element_by_xpath( "//button[@class='mcf__btn -state-secondary ng-star-inserted']").click()
            wait(1)
            web.driver.find_element_by_xpath( "//span[normalize-space()='Search']").click()

            while(True):
                try:
                    web.driver.find_element_by_xpath("//span[normalize-space()='Show Details']").click()
                    break
                except:
                    if 'No matching records found.' in web.get_page_source():
                        return{"message":"no data found or wrong number"}
                    
            places = web.driver.find_elements_by_xpath( "//span[@class='simple-journey-airport']")
            flight_detail = {"doc_no": tracking_id,
                    "cargo_type": web.driver.find_element_by_xpath( '//span[@class="cargo-type"]').text,
                    "jrn_no": web.driver.find_element_by_xpath( "//span[@class='order-id']/b").text,
                    "going from": places[0].text,
                    "going to": places[1].text,
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-2 col-md-2 col-lg-2']/span[1]").text:  # pieces
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-2 col-md-2 col-lg-2']/span[2]").text,  # 4
                    web.driver.find_element_by_xpath( "//span[normalize-space()='Gross Weight']").text:  # gross weight
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-4 col-sm-3 col-md-3 col-lg-3'][1]/span[2]").text,
                # 1217 k
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-4 col-sm-3 col-md-3 col-lg-3'][2]/span[1]").text:
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-4 col-sm-3 col-md-3 col-lg-3'][2]/span[2]").text,
                    web.driver.find_element_by_xpath(
                                    "//div[@class='col-xs-5 col-sm-3 col-md-3 col-lg-3 ng-star-inserted']/span[1]").text:
                    web.driver.find_element_by_xpath(
                                        "//div[@class='col-xs-5 col-sm-3 col-md-3 col-lg-3 ng-star-inserted']/span[2]").text,
                    web.driver.find_element_by_xpath(
                                    "//div[@class='col-xs-5 col-sm-6 col-md-4 col-lg-3 ng-star-inserted']/span[1]").text:
                    web.driver.find_element_by_xpath(
                                        "//div[@class='col-xs-5 col-sm-6 col-md-4 col-lg-3 ng-star-inserted']/span[2]").text,
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-5 col-sm-6 col-md-4 col-lg-4']/span[1]").text:
                    web.driver.find_element_by_xpath( "//div[@class='col-xs-5 col-sm-6 col-md-4 col-lg-4']/span[2]").text,
                    web.driver.find_element_by_xpath( "//b[normalize-space()='SHCs']").text:
                    web.driver.find_element_by_xpath( "//i[@class='black-text']").text                    }
            wait(1)
            # click Function for tracking details
            web.driver.find_element_by_xpath( '//div[@class="row header-row order-status ng-star-inserted"]/div[2]/div/span/span/button').click()
            wait(2)
            # no_stops = web.driver.find_element_by_xpath( "//span[@class='stops ng-star-inserted']").text[1]

            # listbox
            web.driver.find_element_by_xpath( '//ng-select[@role="listbox"][1]').click()
            wait(2)
            web.driver.find_element_by_xpath( "//span[normalize-space()='Least Recent']").click()
            wait(2)

            milestones = web.driver.find_elements_by_xpath( "//ul[@class='milestone']/li")
            print(len(milestones))
            milestones = []

            for i in range(0, len(milestones)):  # loop1
                x = len(web.driver.find_elements_by_xpath( "//ul[@class='milestone']/li[" + str(
                    i + 1) + "]//div"))  # checking number of div tags in each card
                if x == 7:
                    status = \
                        web.driver.find_elements_by_xpath( "(//div[@class='row-container'])[2]//p[@class='milestone-description']")[
                            i].text
                    status_location_time = web.driver.find_element_by_xpath(
                                                                "//ul[@class='milestone']/li[" + str(
                                                                    i + 1) + "]//div[2]/p[1]").text
                    status_date = web.driver.find_element_by_xpath(
                                                        "//ul[@class='milestone']/li[" + str(i + 1) + "]//div[2]/p[2]").text
                    pieces = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(i + 1) + "]//div[5]/p[1]").text
                    grossWeight = web.driver.find_element_by_xpath(
                                                        "//ul[@class='milestone']/li[" + str(i + 1) + "]//div[5]/p[2]").text
                    # locations, Time = separate(status_location_time)
                    data = {"status": status,
                            "status date": status_date,
                            'pieces': pieces,
                            "gross weight": grossWeight,
                            "status location and time": status_location_time}
                    milestones.append(data)

                elif x == 10:  # for the cards with 10 div elements
                    status = \
                        web.driver.find_elements_by_xpath( "(//div[@class='row-container'])[2]//p[@class='milestone-description']")[
                            i].text
                    status_location_time = web.driver.find_element_by_xpath(
                                                                "//ul[@class='milestone']/li[" + str(
                                                                    i + 1) + "]//div[2]/p[1]").text
                    status_date = web.driver.find_element_by_xpath(
                                                        "//ul[@class='milestone']/li[" + str(i + 1) + "]//div[2]/p[2]").text
                    pieces = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(i + 1) + "]//div[5]/p[1]").text
                    grossWeight = web.driver.find_element_by_xpath(
                                                        "//ul[@class='milestone']/li[" + str(i + 1) + "]//div[5]/p[2]").text
                    source = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(
                        i + 1) + "]//span[@class='col-xs-2 col-lg-2']/b").text
                    destination = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(
                        i + 1) + "]//span[@class='col-xs-5 col-lg-2 ']/b").text
                    plannedTimeAtSource = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(
                        i + 1) + "]//div[@class='journey-steps row journey-dates ng-star-inserted']//span[@class='col-xs-7 "
                                    "col-lg-7']").text
                    plannedTimeAtDestination = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(
                        i + 1) + "]//div[@class='journey-steps row journey-dates ng-star-inserted']//span[@class='col-xs-5 "
                                    "col-lg-5 ']").text
                    plannedDateAtSource = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(
                        i + 1) + "]//div[@class='journey-steps journey-dates row ng-star-inserted']//span[@class='col-xs-7 "
                                    "col-lg-7']").text
                    plannedDateAtDestination = web.driver.find_element_by_xpath( "//ul[@class='milestone']/li[" + str(
                        i + 1) + "]//div[@class='journey-steps journey-dates row ng-star-inserted']//span[@class='col-xs-5 "
                                    "col-lg-5 ']").text
                    # locations, Time = separate(status_location_time)
                    data = {"status": status,
                            "status date": status_date,
                            "source": source,
                            "destination": destination,
                            "planned time at source": plannedTimeAtSource,
                            "planned time at destination": plannedTimeAtDestination,
                            "planned date at source": plannedDateAtSource,
                            "planned date at destination": plannedDateAtDestination,
                            'pieces': pieces,
                            "gross weight": grossWeight,
                            "status location and time ": status_location_time
                            }
                    milestones.append(data)
            # Check if 'milestones' or 'flight_detail' lists are empty or wrong number        
            if len(milestones)==0:
              return{"message":"no data found or wrong number"}                

            client = MongoClient('mongodb://localhost:27017')
            db = client.QatarCargo
            collection = db.QC
            collection.insert_one({"milestones": milestones, "flight_details": flight_detail,'complete_number':tracking_id_complete,'airline_code':airline_code,'date':date})
            return {"milestones": milestones, "flight_details": flight_detail}
    
def scrape_KLM_cargo(track_id, air_code):
    # get trcking id from request
    tracking_id_complete = track_id
    tracking_id = track_id
    tracking_id = tracking_id.replace('-', '')
    date = datetime.now().strftime('%m-%d-%Y')
    airline_code=air_code
   
      # Connect to the MongoDB
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC

    # Check if data already exists in MongoDB
    data_in_mongo = collection.find_one({'complete_number':tracking_id_complete,'airline_code':airline_code,'date':date})  # Find one document, you can add specific query criteria


    if data_in_mongo is not None:
        # Check if the data in MongoDB is from today's date
        today = datetime.now().date()
        mongo_date = data_in_mongo.get('date', None)

    
        # Data from today's date, return it
        milestones = data_in_mongo.get('milestones', [])
        flight_detail = data_in_mongo.get('flight_detail', [])
        shipment_detail = data_in_mongo.get('shipment_detail', [])

        return {
            "message": "Data loaded from MongoDB",
            "milestones": milestones,
            "flight_detail": flight_detail,
            "shipment_detail": shipment_detail
        }
    else:  
        web = Browser()
# ... (The scraping part of your code, same as before)
        web.driver.get("https://www.afklcargo.com/mycargo/shipment/singlesearch")
        wait(2)
        web.driver.maximize_window()
        wait(2)
        input = web.driver.find_element_by_xpath('//textarea[@placeholder="AWB starts with 074 or 057"]')
        input.send_keys(tracking_id)
        textbox = web.driver.find_element_by_xpath('//button[@type="submit"]')
        wait(2)
        textbox.click()
        wait(2)
        shipment_detail = {"pieces_weight_volume": web.driver.find_element_by_xpath('//div[@class="tnt-booking-bloc"]//li[4]').text
                   }
        wait(2)
        listt =web.driver.find_element_by_xpath('//li[@class="nav-item"]')
        wait(2)
        listt.click()
        wait(2)
        # print(shipment_detail)
# print(shipment_detail)
        # elements = web.driver.find_elements_by_xpath('//*[@style="text-decoration: none;"]')
        # wait(2)
        flight_detail = []
        elements = web.driver.find_elements_by_xpath('//*[@style="text-decoration: none;"]')
        wait(2)
        for i in range(0, len(elements), 4):
            try:
                fromm_to = elements[i].text
                flight_number = elements[i + 1].text
                departure_and_arrival_date_time = elements[i + 2].text
                pieces = elements[i + 3].text

                data3 = {"from_to": fromm_to, "flight_number": flight_number, "departure_and_arrival_date_time": departure_and_arrival_date_time, "pieces": pieces}
                flight_detail.append(data3)
            except Exception as e:
                break

        # Print the final flight_detail list outside the loop
        # print(flight_detail)

        milestones = web.driver.find_elements_by_xpath('//div[@class="tab-content"]//li')
        milestones=[]
        wait(2)
        # print(len(milestones))
        for i in range(0, len(milestones)):
                    date_time = milestones[i].find_element_by_xpath("span[1]").text
                    location = milestones[i].find_element_by_xpath("span[2]").text
                    status_code = milestones[i].find_element_by_xpath("span[3]").text
                    description= milestones[i].find_element_by_xpath("span[4]").text

                    # Call the removeSpaces function to clean up the extracted data
                    # date_time = removeSpaces(date_time)
                    # location = removeSpaces(location)
                    # status_code = removeSpaces(status_code)
                    # description = removeSpaces(description)

                    data1 = {"date_time": date_time,"location":location,"status_code": status_code,"description":description}
                    milestones.append(data1)
                    client = MongoClient('mongodb://localhost:27017')
                    db = client.QatarCargo
                    collection = db.QC
                    collection.insert_one({"milestones": milestones, "flight_details": flight_detail,"shipment_detail":shipment_detail,'complete_number':tracking_id_complete,'airline_code':airline_code,'date':date})
                    return {"milestones": milestones, "flight_details": flight_detail,"shipment_detail":shipment_detail}



def scrape_Silkway_cargo(track_id,air_code):
    airline_code = air_code
    date = datetime.now().strftime('%m-%d-%Y')
    tracking_id_complete=track_id
    # tracking_id=track_id
    # id_parts = tracking_id.split('-')
    # tracking_id= id_parts[-1]   
    # Connect to the MongoDB
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC

    # # Check if data already exists in MongoDB
    data_in_mongo = collection.find_one({'complete_number': tracking_id_complete, 'airline_code': air_code,'date':date})
    if data_in_mongo is not None:
        # Check if the data in MongoDB is from today's date
        today = datetime.now().date()
        mongo_date = data_in_mongo.get('date', None)
        # Data from today's date, return it
        milestone = data_in_mongo.get('milestone', [])
        flight_detail = data_in_mongo.get('flight_detail', [])
        truck_detail = data_in_mongo.get('truck_detail', [])

        return {
            "message": "Data loaded from MongoDB",
            "milestone": milestone,
            "flight_detail": flight_detail,
            "truck_detail": truck_detail
        }
    else:
        web=Browser()
        web.driver.get("https://sww.enxt.solutions/enxt/iframe/track-and-trace/{}".format(track_id))
        wait(1)
        web.driver.maximize_window()
        wait(3)
        while(True):
                try:
                    web.driver.find_element_by_xpath('//span[contains(text(), "Show more")]/mat-icon').click()
                    break
                except:
                    if 'This AWB does not exist. Please, double-check the AWB number.' in web.get_page_source():
                        return{"message":"no data found or wrong number"}
        # Format for converting the date and time to a string
        out_form = '%Y-%m-%d %H:%M:%S'
        # Format for parsing the date and time from a string
        in_form = '%A-%d-%b-%Y %H:%M'

        shipment_detail = {"actual_weight": web.driver.find_element_by_xpath('//div[@class="track-and-trace__content tt-report ng-tns-c652-0 ng-star-inserted"]/div[2]/div/div[1]/span').text,
                   "volume": web.driver.find_element_by_xpath('//div[@class="track-and-trace__content tt-report ng-tns-c652-0 ng-star-inserted"]/div[2]/div/div[2]/span').text,
                   "pieces": web.driver.find_element_by_xpath('//div[@class="track-and-trace__content tt-report ng-tns-c652-0 ng-star-inserted"]/div[2]/div/div[3]/span').text
            }
        wait(2)
        # print(shipment_detail)
        flight_details = web.driver.find_elements_by_xpath('//tbody[@role="rowgroup"]/tr')
        print(len(flight_details))
        flight_detail = []  # Initialize an empty list

        for i in range(0, len(flight_details)):
            try:
                departure = flight_details[i].find_element_by_xpath('td[2]').text
                arrival = flight_details[i].find_element_by_xpath("td[3]").text
                carrier = flight_details[i].find_element_by_xpath("td[4]").text
                flight_number = flight_details[i].find_element_by_xpath("td[5]").text
                flight_date = flight_details[i].find_element_by_xpath("td[6]").text    
                flight_status = flight_details[i].find_element_by_xpath("td[10]").text    
                data1 = {"departure": departure,"arrival": arrival,"carrier":carrier,"flight_number":flight_number,"flight_date": flight_date,"flight_status":flight_status}
                flight_detail.append(data1)
            except Exception as e:    
                pass
        milestone_elements = web.driver.find_elements_by_xpath('//div[contains(@class,"tt-report__fsu")]/app-track-and-trace-fsu/div/div/ul/li')
        print(len(milestone_elements))

        milestones = []  # Initialize an empty list
        previous_location = ''  # Initialize a variable to store the location of the previous element

        for i in range(len(milestone_elements)):
            try:
                milestone_datee = milestone_elements[i].find_element_by_xpath('div[3]/i').text
                status = milestone_elements[i].find_element_by_xpath("div[3]/span[1]").text
                description = milestone_elements[i].find_element_by_xpath("div[3]/span[2]").text

                # Check if location is empty, use the previous location if needed
                location = milestone_elements[i].find_element_by_xpath("div[1]").text
                if not location:
                    location = previous_location

                # Update the previous location for the next iteration
                previous_location = location

                # Add other fields if needed
                data1 = {"location": location, "date":milestone_datee, "description": description, "status": status}
                milestones.append(data1)
            except Exception as e:
                pass

            if len(milestones)==0 and len(flight_detail)==0 and len(shipment_detail)==0:

               return{"message":"no data found or wrong number"}        

       
       
# ... (The scraping part of your code, same as before)
        
        
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC
    collection.insert_one({"milestone": milestones, "flight_detail": flight_detail,"shipment_detail":shipment_detail,'complete_number':tracking_id_complete,'airline_code':air_code,'date':date})
    # # Return a JSON response with the scraped data
    return {"message": "Data Loading", "milestone": milestones, "flight_detail": flight_detail,"shipment_detail":shipment_detail}


def c(track_id, air_code):
    # get tracking id from request
    airline_code = air_code
    date = datetime.now().strftime('%m-%d-%Y')
    tracking_id_complete=track_id
    tracking_id=track_id
    id_parts = tracking_id.split('-')
    tracking_id= id_parts[-1]   
    # Connect to the MongoDB
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC

    # Check if data already exists in MongoDB
    data_in_mongo = collection.find_one({'complete_number': tracking_id_complete, 'airline_code': airline_code, 'date': date})

    if data_in_mongo is not None:
        # Check if the data in MongoDB is from today's date
        today = datetime.now().date()
        mongo_date = data_in_mongo.get('date', None)

        # Data from today's date, return it
        milestone = data_in_mongo.get('milestone', [])
        flight_detail = data_in_mongo.get('flight_detail', [])
        shipment_detail = data_in_mongo.get('shipment_detail', [])

        return {
            "message": "Data loaded from MongoDB",
            "milestone": milestone,
            "flight_detail": flight_detail,
            "shipment_detail": shipment_detail
        }
    else:

        # Add your scraping logic for Kuwait Airways here
        # Example:
        web = Browser()
        web.driver.get("https://www.kuwaitairways.com/en/cargo/tracking")
        web.driver.maximize_window()
        wait(2)
        input = web.driver.find_element_by_xpath('//input[@id="txtAwbNo"]')
        input.send_keys(tracking_id)
        wait(2)
        accept=web.driver.find_element_by_xpath('//a[normalize-space()="Accept Cookies"]')
        accept.click()
        wait(2)
        # web.driver.find_element_by_xpath('//input[@id="btnSubmit"]').click()
        # # web.driver.execute_script("arguments[0].scrollIntoView();", e)

        web.driver.find_element_by_xpath('//input[@id="btnSubmit"]').click()
        wait(10)
        while(True):
                try: 
                    flight_details = web.driver.find_elements_by_xpath('//*[@class="table-holder"][1]/table/tbody/tr')
                    break
                except:
                    if 'Please check your request and try again.' in web.get_page_source():
                        return{"message":"no data found or wrong number"}
        wait(2)            
        shipment_detail = {"shipment_id": web.driver.find_element_by_xpath('//span[@id="lblShipmentInfo"]').text,
                            "status_weight_time": web.driver.find_element_by_xpath('//span[@id="lblCurStatus"]').text
                                
                            }
        wait(2)
        # flight_details = web.driver.find_elements_by_xpath('//*[@class="table-holder"][1]/table/tbody/tr')
        # # print("Number of flight details:", len(flight_details))
        flight_detail = []  # Initialize an empty list
        for i in range(0, len(flight_details)):
            try:
                flight_no = flight_details[i].find_element_by_xpath('td[1]').text
                flight_date = flight_details[i].find_element_by_xpath('td[2]').text
                origin = flight_details[i].find_element_by_xpath('td[3]').text
                destination = flight_details[i].find_element_by_xpath('td[4]').text
                piece = flight_details[i].find_element_by_xpath('td[5]').text    
                volume = flight_details[i].find_element_by_xpath('td[7]').text
                status = flight_details[i].find_element_by_xpath('td[8]').text        
                data1 = {"flight_no": flight_no, "flight_date": flight_date, "origin": origin, "destination": destination, "piece": piece, "volume": volume, "status": status}
                flight_detail.append(data1)
            except Exception as e:
                pass

        wait(2)
        milestones = web.driver.find_elements_by_xpath('//*[@class="table-holder"][2]/table/tbody/tr')
        print(len(milestones))
        # Process and clean up the extracted data
        milestone = []
        for i in range(len(milestones)):
                try:
                    status = milestones[i].find_element_by_xpath('td[1]').text
                    airport = milestones[i].find_element_by_xpath('td[2]').text
                    milestone_date= milestones[i].find_element_by_xpath('td[3]').text
                    detail = milestones[i].find_element_by_xpath('td[4]').text

                    data1 = {"status": status, "airport": airport, "date": milestone_date, "detail": detail}
                    milestone.append(data1)
                except:
                    continue   
        client = MongoClient('mongodb://localhost:27017')
        db = client.QatarCargo
        collection = db.QC
        collection.insert_one({"milestone": milestone, "flight_detail": flight_detail,"shipment_detail":shipment_detail,'complete_number':tracking_id_complete,'airline_code':air_code,'date':date})
        # # Return a JSON response with the scraped data
        return {"message": "Data Loading", "milestone": milestone, "flight_detail": flight_detail,"shipment_detail":shipment_detail}

def scrape_avianca_cargo(track_id, airline_code):
    # Get current date
    date = datetime.now().strftime('%m-%d-%Y')
    tracking_id = track_id
    airline_code = airline_code

    # MongoDB setup for Qatar Cargo
    client = MongoClient('mongodb://localhost:27017')
    db = client.QatarCargo
    collection = db.QC

    # Check if data is already present in MongoDB
    data_in_mongo = collection.find_one({'complete_number': tracking_id, 'airline_code': airline_code, 'date': date})
    
    # If data is found in MongoDB, return it
    if data_in_mongo is not None:
        # Check if the data in MongoDB is from today's date
        today = datetime.now().date()
        mongo_date = data_in_mongo.get('date', None)

        # Data from today's date, return it
        milestone = data_in_mongo.get('Milestones', [])
        pieces_volume = data_in_mongo.get('piece_volume', [])
        origin_destination = data_in_mongo.get('Origin_destination', [])

        return {
            "message": "Data loaded from MongoDB",
            "milestone": milestone,
            "piece_volume": pieces_volume,
            "Origin_destination": origin_destination
        }

    else:
        # Set up the web scraping
        web = Browser()
        web.driver.get("https://avianca-icargo.ibsplc.aero/icargoportal/portal/trackshipments?trkTxnValue={}".format(tracking_id))
        wait(1)
        
        # Try to get origin and destination
        while True:
            try:
                origin_destination = web.driver.find_element_by_xpath('//span[@class=" pull-right fligh-way-tab"]').text
                break
            except:
                # If 'Non Standard AWB' is in the page source, it indicates no data found or wrong number
                if 'Non Standard AWB ' in web.get_page_source():
                    return {"message": "no data found or wrong number"}

        web.driver.maximize_window()
        wait(3)

        # Get piece volume information
        pieces_volume = web.driver.find_element_by_xpath('//div[@class="carousel-caption"]/label[2]').text

        # Get milestones
        milestones = web.driver.find_elements_by_xpath('//div[@class="col-md-12  "]/div[1]/div[1]/div')
        resp = {
            "piece_volume": pieces_volume,
            "Origin_destination": origin_destination,
            "Milestones": []
        }

        # Iterate through milestones and extract information
        for i in range(len(milestones)):
            try:
                status = milestones[i].find_element_by_xpath('div[1]/div[1]').text
                milestone_date = milestones[i].find_element_by_xpath('div[1]/div[2]').text
                flight_no = milestones[i].find_element_by_xpath('div[1]/div[4]').text

                date = removeSpaces(date)
                res = {
                    "Date": milestone_date,
                    "Description": status,
                    "FlightNumber": flight_no
                }
                resp["Milestones"].append(res)
            except:
                continue

        # Convert to JSON format
        output_json = json.dumps({
            "piece_volume": pieces_volume,
            "Origin_destination": origin_destination,
            "Milestones": resp["Milestones"]
        }, ensure_ascii=False)

        # Insert data into MongoDB
        client = MongoClient('mongodb://localhost:27017')
        db = client.QatarCargo
        collection = db.QC
        collection.insert_one({
            "Milestones": resp["Milestones"],
            "piece_volume": pieces_volume,
            "Origin_destination": origin_destination,
            'complete_number': tracking_id,
            'airline_code': airline_code,
            'date': date
        })

        return output_json



@app.route('/scrape', methods=['GET'])
def scrape_cargo():
    tracking_id = request.args.get('number')
    airline_code = request.args.get('airline_code')
    date = datetime.now().strftime('%m-%d-%Y')

    if airline_code == 'QR':
        cargo_data = scrape_Qatar_cargo(tracking_id, airline_code)
    elif airline_code == 'EK':
        cargo_data = scrape_Emirates_cargo(tracking_id, airline_code)
    elif airline_code == 'KL':
        cargo_data = scrape_KLM_cargo(tracking_id, airline_code)
    elif airline_code == 'SW':  # Add a condition for Silkway cargo
        cargo_data = scrape_Silkway_cargo(tracking_id,airline_code)
    # elif airline_code == 'KU':  # Add a condition for Silkway cargo
    #     cargo_data = scrape_Kuwait_cargo(tracking_id,airline_code)
    elif airline_code == 'QT':
        cargo_data = scrape_avianca_cargo(tracking_id, airline_code)        
    else:
        cargo_data = {"message": "Invalid airline code"}

    # Store cargo data in MongoDB
    collection = db.CargoData
    collection.insert_one({
        "tracking_id": tracking_id,
        "airline_code": airline_code,
        "data": cargo_data,
        "date": date
    })

    # Check cargo_data and return a valid response
    if cargo_data:
        return jsonify(cargo_data)
    else:
        return jsonify({"message": "Error processing cargo data"})
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)








