from flask import make_response, send_file
from pymongo import MongoClient
#to get Object Id from mongodb
from bson.objectid import ObjectId
#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os
#to compare UUID
# from bson.binary import UuidRepresentation
# from uuid import UUID

#to get current year
import datetime

import xlsxwriter
import io

load_dotenv(find_dotenv())
mongo_password = os.environ.get("MONGO_PWD")
connection_string = f"mongodb+srv://admin:{mongo_password}@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string, UuidRepresentation="standard")
salespipeline = client.SalesPipeline
dropDownDB = salespipeline.dropDownData

def getAllYears():
    try:
        result = list(salespipeline.list_collection_names())
        # print(result)
        years = []
        for c in result:
            if c.startswith("Year") and c.endswith("Data"):
                c = c.replace("Year","")
                c = c.replace("Data","")
                years.append(int(c))
        # print(years)
        current_year = datetime.date.today().year
        # print(type(current_year))

        years.remove(current_year)
        # print(years)
        
        return make_response({"current":current_year,"archieve":years}, 200)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)

def getDropDownData():
    try:
        current_year = datetime.date.today().year
        result = dropDownDB.find({'Year':current_year},{'_id':0})[0]
        # print(result)
        return make_response({"message":result}, 200)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)

def addSalesRecord(data):
    try:
        # print(data)
        if '2024' in data:
            data = data['2024']
            # print(data)
            

            count = salespipeline.Year2024Data.count_documents({})
            # print(count)
            salespipeline.Year2024Data.insert_one(data)

            
            if count+1 == salespipeline.Year2024Data.count_documents({}):
                updateDropDown(data)
                return make_response({"message":"Sales Record Added"}, 200) 
            else:
                return make_response({"ERROR":"Sale Record Not Added"}, 500)
        else:
            return make_response({"ERROR":"Error in sending json"}, 500)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)

def getAllSalesRecords(year):
    try:
        # print(type(year))
        if year == 2024:
            data = list(salespipeline.Year2024Data.find())
            # print(data)
        elif year == 2023:
            data = salespipeline.Year2023Data.find()
        elif year == 2022:
            data = salespipeline.Year2022Data.find()
        else:
            return make_response({"ERROR":"No data for the year"})
        # print(list(data))  
        data_obj={}
        for index,sale in enumerate(data, start=1):
            data_obj[index] = sale
            data_obj[index]['_id'] = str(data_obj[index]['_id'])
        # print(data_obj)


        calculations = getAllCalculations(year)

        return make_response({"message":data_obj,"calculation":calculations}, 200)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    
def editSalesRecord(data):
    # print(data)
    try:
        if '2024' in data:
            data = data['2024']
            # print(data)
            editDropDown(data)
            updateDropDown(data)
            # SaleNumber = int(data['SaleNumber'])
            try:
                _id = ObjectId(data['_id'])
            except:
                return make_response({"ERROR":"Wrong _id"}, 404)
            data.pop("_id",None)
            # print(data)
            data_obj = {
                "$set":data
            }
            if(salespipeline.Year2024Data.count_documents({"_id":_id},limit = 1) == 1):
                salespipeline.Year2024Data.update_one({"_id":_id}, data_obj) 
                return make_response({"message":"Data Edited"}, 201)
            else:
                return make_response({"message":"No record Found"},202)
            
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    
def deleteSalesRecord(data):
    try:
        if '2024' in data:
            data = data['2024']
            try:
                _id = ObjectId(data['_id'])
            except:
                return make_response({"ERROR":"Wrong _id"}, 404)
            # print(SaleNumber)

            #delete from dropdown - Customers only
            #data got from db
            dbData = list(salespipeline.Year2024Data.find({'_id':ObjectId(_id)},{'_id':0}))[0]
            # print(dbData)
            dbCustomer = dbData['Customer']

            #get data of dropdown
            result = dropDownDB.find_one({},{'_id':0})

            # if Customer != dbCustomer and Customer not in result['Customers']:
                #check whether any other record has that Customer or not
            freq_map_cust = getFrequencies('Customer')
            if freq_map_cust[dbCustomer] == 1:
                dropDownDB.update_one({},{"$pull":{'Customers':dbCustomer}})
                

            result = salespipeline.Year2024Data.delete_one({'_id':_id})
            # print(result)
            if result.deleted_count > 0:
                return make_response({"message":"Sale Record Deleted"}, 200)
            else:
                return make_response({"ERROR":"No Sale Record Match SaleNumber"}, 404)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)


def updateDropDown(data):
    # print(data)
    result = dropDownDB.find_one({},{'_id':0})
    # print(result)
    current_year = datetime.date.today().year
    Year = result['Year']
    # print(Year)
    if Year != current_year:
        new_obj = {
            "$set":{
                'Year':current_year
            }
        }
        dropDownDB.update_one({},new_obj)
    
    Customer = data['Customer']
    Channel = data['Channel']
    Reseller = data['Reseller']
    EC_PointOfContact = data['EC_PointOfContact']
    Stage = data['Stage']
    ChancesOfWinning = data['ChancesOfWinning']
    WonLost = data['WonLost']
    # print(Customer,Channel, Reseller, EC_PointOfContact, Stage, ChancesOfWinning, WonLost)
    # print(result['Customers'])

    if Customer not in result['Customers']:
        dropDownDB.update_one({},{"$push":{'Customers':Customer}})
    if Channel not in result['Channel']:
        dropDownDB.update_one({},{"$push":{'Channel':Channel}})
    if Reseller not in result['Reseller']:
        dropDownDB.update_one({},{"$push":{'Reseller':Reseller}})
    if EC_PointOfContact not in result['EC_PointOfContact']:
        dropDownDB.update_one({},{"$push":{'EC_PointOfContact':EC_PointOfContact}})
    if Stage not in result['Stage']:
        dropDownDB.update_one({},{"$push":{'Stage':Stage}})
    if ChancesOfWinning not in result['ChancesOfWinning']:
        dropDownDB.update_one({},{"$push":{'ChancesOfWinning':ChancesOfWinning}})
    if WonLost not in result['WonLost']:
        dropDownDB.update_one({},{"$push":{'WonLost':WonLost}})

def editDropDown(data):
    # print(data)
    #edit data that was sent from frontend
    _id = data['_id']
    Customer = data['Customer']

    #data got from db
    dbData = list(salespipeline.Year2024Data.find({'_id':ObjectId(_id)},{'_id':0}))[0]
    # print(dbData)
    dbCustomer = dbData['Customer']


    #get data of dropdown
    result = dropDownDB.find_one({},{'_id':0})

    if Customer != dbCustomer and Customer not in result['Customers']:
        #check whether any other record has that Customer or not
        freq_map = getFrequencies('Customer')
        if freq_map[dbCustomer] == 1:
            dropDownDB.update_one({},{"$pull":{'Customers':dbCustomer}})
        dropDownDB.update_one({},{"$push":{'Customers':Customer}})
    
    # if Channel != dbChannel and Channel not in result['Channel']:
    #     #check whether any other record has that Customer or not
    #     freq_map = getFrequencies()
    #     if freq_map[dbChannel] == 1:
    #         dropDownDB.update_one({},{"$pull":{'Channel':dbChannel}})
    #     dropDownDB.update_one({},{"$push":{'Channel':dbChannel}})
    
def getFrequencies(field):
    allDbData = list(salespipeline.Year2024Data.find())
    freq_map = {}

    for doc in allDbData:
        freq_map[doc.get(f'{field}')] = freq_map.get(doc.get(f'{field}'), 0) + 1
    return freq_map


def getAllCalculations(year):
    try:
        if year == 2024:
            #do this
            data = list(salespipeline.Year2024Data.find({},{'_id':0, 'ProjectSize':1}))
            # print(list(data))
            updateCalculations(year,data)

        elif year == 2023:
            #do this
            data = list(salespipeline.Year2023Data.find({},{'_id':0, 'ProjectSize':1}))
            # print(data)
            updateCalculations(year,data)

        elif year == 2022:
            #do this
            data = list(salespipeline.Year2022Data.find({},{'_id':0, 'ProjectSize':1}))
            # print(list(data))
            updateCalculations(year,data)
        result = list(salespipeline.CalculationData.find({'year':year},{'_id':0,'data':1}))[0]['data']
        # print(result)
        # result['Current_Year_Total'] = f'{result['Current_Year_Total']:,}'
        # result['Prior_Year_Total'] = f'{result['Prior_Year_Total']:,}'
        # result['Current_Year_Target_Goal'] = f'{result['Current_Year_Target_Goal']:,}'
        # result['Goal_Achievement'] = f'{result['Goal_Achievement']:,}'

        result['Current_Year_Total'] = f"{result['Current_Year_Total']:,}"
        result['Prior_Year_Total'] = f"{result['Prior_Year_Total']:,}"
        result['Current_Year_Target_Goal'] = f"{result['Current_Year_Target_Goal']:,}"
        result['Goal_Achievement'] = f"{result['Goal_Achievement']:,}"
        
        # print(result)
        return (result)
    except Exception as e:
        return (str(e))

def updateCalculations(year, data):
    try:
        numeric_values = []
        for val in data:
            val = val['ProjectSize']
            val = val.replace(',','')
            val = val.strip()
            if val!=' ' and val.isnumeric():
                numeric_values.append(float(val))
        # print(numeric_values)
        current_year_total = sum(numeric_values)
        result = list(salespipeline.CalculationData.find({'year':year},{'_id':0,'data':1}))[0]['data']
        # print(result)
        previous_year_total= 0.0
        #get previous years total
        if year != 2022:
            previous_year_total = list(salespipeline.CalculationData.find({'year':year-1},{'_id':0,'data':1}))[0]['data']
        # print(previous_year_total)
            previous_year_total = previous_year_total['Current_Year_Total']
        # print(previous_year_total)
        result['Current_Year_Total'] = round(current_year_total,2)
        result['Prior_Year_Total'] = round(previous_year_total,2)
        result['Current_Year_Target_Goal'] = round(+result['Prior_Year_Total']*1.3,2)
        result['Goal_Achievement'] = round(+result['Current_Year_Total']-result['Current_Year_Target_Goal'], 2)
        # print(f'{round(current_year_total,2):,}')
        # print(result)

        result = {
            '$set':{
                'data':result
            }
        }

        salespipeline.CalculationData.update_one({'year':year},result)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    

def downloadExcel():
    try:
        #create excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        # workbook = xlsxwriter.Workbook("SalesPipeline.xlsx")
        # worksheet = workbook.add_worksheet("CurrentYear")
        
        #year 2024
        data2024 = list(salespipeline.Year2024Data.find({},{'_id':0}))
        worksheet = createExcel(workbook, data2024, 2024)

        #year 2023
        data2023 = list(salespipeline.Year2023Data.find({},{'_id':0}))
        worksheet = createExcel(workbook, data2023, 2023)

        data2022 = list(salespipeline.Year2022Data.find({},{'_id':0}))
        worksheet = createExcel(workbook, data2022, 2022)

        workbook.close()
                
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="SalesPipeline.xlsx",
        )

        # return make_response({"message":'true'}, 200)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    

def createExcel(workbook, data, year):

    worksheet = workbook.add_worksheet(f"Year {year}")
     #cell formating
    blue_text_wrap_format = workbook.add_format()
    blue_text_wrap_format.set_text_wrap(True)
    blue_text_wrap_format.set_bg_color('#000099')
    blue_text_wrap_format.set_font_color('#FFFFFF')
    blue_text_wrap_format.set_align('center')
    blue_text_wrap_format.set_bold(True)
    

    bold_centre_format = workbook.add_format()
    bold_centre_format.set_bold(True)
    bold_centre_format.set_align('center')

    right_format = workbook.add_format()
    right_format.set_align('right')


    #set the column width
    worksheet.set_column(0,0, 30)
    worksheet.set_column(1,1, 20)
    worksheet.set_column(2,2, 15)
    worksheet.set_column(8,8, 23)
    worksheet.set_column(9,9, 15)
    worksheet.set_column(10,10, 20)
    worksheet.set_column(13,13, 10)
    worksheet.set_column(14,14, 30)

    worksheet.set_column(3,3, 10)
    worksheet.set_column(4,4, 10)
    worksheet.set_column(5,5, 10)
    worksheet.set_column(6,6, 10)
    worksheet.set_column(11,11, 10)
    worksheet.set_column(12,12, 10)
    worksheet.set_column(7,7, 10)

    


    #enter data to excel
    worksheet.write(0,0, "ENCRYPTION CONSULTING, LLC",bold_centre_format)

    today = datetime.date.today().strftime(f"%m-%d-%Y")
    # print(today)
    worksheet.write(1,0, today, bold_centre_format)

    worksheet.write(2,0, "SALES SPREADSHEET", bold_centre_format)

    #calculations
    worksheet.write(0,8, "Current Year Project Total:", bold_centre_format)
    worksheet.write(1,8, "Prior Year Project Total:",bold_centre_format)
    worksheet.write(2,8, "Current Year Target Goal:",bold_centre_format)
    worksheet.write(3,8, "Goal Achievement:",bold_centre_format)

    calculations = getAllCalculations(year)
    # print(calculations)
    worksheet.write(0,9, calculations['Current_Year_Total'], right_format)
    worksheet.write(1,9, calculations['Prior_Year_Total'], right_format)
    worksheet.write(2,9, calculations['Current_Year_Target_Goal'], right_format)
    worksheet.write(3,9, calculations['Goal_Achievement'], right_format)

    #write columns
    worksheet.write(7,0, "Customer", blue_text_wrap_format)
    worksheet.write(7,1, "Type of Project", blue_text_wrap_format)
    worksheet.write(7,2, "Channel", blue_text_wrap_format)
    worksheet.write(7,3, "Reseller", blue_text_wrap_format)
    worksheet.write(7,4, "EC Point of Contact", blue_text_wrap_format)
    worksheet.write(7,5, "Cient Point of Contact", blue_text_wrap_format)
    worksheet.write(7,6, "Client POC Email", blue_text_wrap_format)
    worksheet.write(7,7, "Date Sold", blue_text_wrap_format)
    worksheet.write(7,8, "Quarter", blue_text_wrap_format)
    worksheet.write(7,9, "Year", blue_text_wrap_format)
    worksheet.write(7,10, "Stage", blue_text_wrap_format)
    worksheet.write(7,11, "Project Size", blue_text_wrap_format)
    worksheet.write(7,12, "Chances of Winning", blue_text_wrap_format)
    worksheet.write(7,13, "Won/Lost", blue_text_wrap_format)
    worksheet.write(7,14, "Notes on Follow", blue_text_wrap_format)

    last_row = 0
    #enter the data
    for index, entry in enumerate(data):
        worksheet.write(8+index, 0, entry['Customer'])
        worksheet.write(8+index, 1, entry['TypeOfProject'])
        worksheet.write(8+index, 2, entry['Channel'])
        worksheet.write(8+index, 3, entry['Reseller'])
        worksheet.write(8+index, 4, entry['EC_PointOfContact'])
        worksheet.write(8+index, 5, entry['Client_PointOfContact'])
        worksheet.write(8+index, 6, entry['Client_POC_Email'])
        worksheet.write(8+index, 7, entry['DateSold'])
        worksheet.write(8+index, 8, entry['Quarter'])
        worksheet.write(8+index, 9, entry['Year'])
        worksheet.write(8+index, 10, entry['Stage'])
        worksheet.write(8+index, 11, entry['ProjectSize'])
        worksheet.write(8+index, 12, entry['ChancesOfWinning'])
        worksheet.write(8+index, 13, entry['WonLost'])
        worksheet.write(8+index, 14, entry['NotesOnFollow'])
        last_row = 8+index

    for col in range(15):  # Columns 0 to 14
        worksheet.write(last_row+2, col, None, blue_text_wrap_format)

    return worksheet