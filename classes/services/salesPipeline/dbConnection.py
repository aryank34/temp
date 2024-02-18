from flask import make_response
from pymongo import MongoClient
#to get Object Id from mongodb
# from bson.objectid import ObjectId
#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os
#to compare UUID
# from bson.binary import UuidRepresentation
# from uuid import UUID

#to get current year
import datetime


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
        result = dropDownDB.find({},{'_id':0})[0]
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
            updateDropDown(data)

            #check SaleNumber
            last_sale = salespipeline.Year2024Data.find_one({},{"_id":0,"SaleNumber":1}, sort=[("SaleNumber", -1)])
            # print(last_sale)
            data['SaleNumber'] = last_sale['SaleNumber']+1
            # print(data)

            salespipeline.Year2024Data.insert_one(data)
            

            return make_response({"message":"Sales Record Added"}, 200) 
        else:
            return make_response({"ERROR":"Error in sending json"}, 500)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)

def getAllSalesRecords(year):
    try:
        # print(type(year))
        if year == 2024:
            data = salespipeline.Year2024Data.find({},{'_id':0})
        elif year == 2023:
            data = salespipeline.Year2023Data.find({},{'_id':0})
        elif year == 2022:
            data = salespipeline.Year2022Data.find({},{'_id':0})
        else:
            return make_response({"ERROR":"No data for the year"})
        # print(list(data))  
        data_obj={}
        for sale in data:
            data_obj[sale['SaleNumber']] = sale

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
            updateDropDown(data)
            SaleNumber = int(data['SaleNumber'])
            data_obj = {
                "$set":data
            }
            if(salespipeline.Year2024Data.count_documents({"SaleNumber":SaleNumber},limit = 1) == 1):
                salespipeline.Year2024Data.update_one({"SaleNumber":SaleNumber}, data_obj) 
                return make_response({"message":"Data Edited"}, 201)
            else:
                return make_response({"message":"No record Found"},202)
            
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    
def deleteSalesRecord(data):
    try:
        if '2024' in data:
            data = data['2024']
            SaleNumber = int(data['SaleNumber'])
            # print(SaleNumber)
            result = salespipeline.Year2024Data.delete_one({'SaleNumber':SaleNumber})
            # print(result)
            if result.deleted_count > 0:
                return make_response({"message":"Sale Record Deleted"}, 200)
            else:
                return make_response({"ERROR":"No Sale Record Match SaleNumber"}, 404)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)


def updateDropDown(data):
    result = dropDownDB.find({},{'_id':0})[0]
    # print(result)
    Customer = data['Customer']
    Channel = data['Channel']
    Reseller = data['Reseller']
    EC_PointOfContact = data['EC_PointOfContact']
    Stage = data['Stage']
    ChancesOfWinning = data['ChancesOfWinning']
    WonLost = data['Won/Lost']
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
    if WonLost not in result['Won/Lost']:
        dropDownDB.update_one({},{"$push":{'Won/Lost':WonLost}})


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