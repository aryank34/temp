from flask import Blueprint, request, make_response
from ..loginAuth.tokenAuth import tokenAuth
from .dbConnection import addSalesRecord, getAllSalesRecords, getDropDownData, editSalesRecord, deleteSalesRecord, getAllYears, downloadExcel
from .dbConnection import displayData, addData, editData, deleteData, transferCurrentToSale
auth = tokenAuth()

salesPipelineView = Blueprint('salesPipelineView',__name__)

@salesPipelineView.route("/dashboard/salespipeline/<year>/<type>", methods=['GET'])
@auth.token_auth("/dashboard/salespipeline/<year>/<type>")
def getYearData(year,type):
    if request.method == 'GET':
        # print(year)
        return displayData(int(year), str(type))

@salesPipelineView.route("/dashboard/salespipeline/<year>/<type>/add", methods=['GET', 'POST'])
@auth.token_auth("/dashboard/salespipeline/<year>/<type>/add")
def addRecord(year,type):
    #GET method for dropdown data

    if request.method == 'POST':
        return addData(request.json, int(year),str(type))


@salesPipelineView.route("/dashboard/salespipeline/<year>/<type>/edit", methods=['GET', 'PUT'])
@auth.token_auth("/dashboard/salespipeline/<year>/<type>/edit")
def editRecord(year, type):
    #GET method for dropdown data

    if request.method == 'PUT':
        return editData(request.json, int(year), str(type))


@salesPipelineView.route("/dashboard/salespipeline/<year>/<type>/delete", methods=['DELETE'])
@auth.token_auth("/dashboard/salespipeline/<year>/<type>/delete")
def deleteRecord(year, type):
    if request.method == 'DELETE':
        return deleteData(request.json, int(year), str(type))


@salesPipelineView.route("/dashboard/salespipeline/<year>/current/transfer", methods=['GET', 'POST'])
@auth.token_auth("/dashboard/salespipeline/<year>/current/transfer")
def transferRecord(year):
    #GET method for dropdown

    if request.method == 'POST':
        #from current to sale
        return transferCurrentToSale(request.json, int(year))








#----------------------------------------------------------------------------------------

@salesPipelineView.route("/dashboard/salespipeline", methods=['GET'])
@auth.token_auth("/dashboard/salespipeline")
def getYears():
    if request.method == 'GET':
        return getAllYears()

#@salesPipelineView.route("/dashboard/salespipeline/<year>", methods=['GET'])
#@auth.token_auth("/dashboard/salespipeline/<year>")
# @auth.token_auth("/dashboard/salespipeline/2024")
# @auth.token_auth("/dashboard/salespipeline/2023")
# @auth.token_auth("/dashboard/salespipeline/2022")
def getSalesPipeline(year):
    if request.method == 'GET':
        #send all the documents present in db accoring to current year
        # print(year)
        #calculations included in result
        result = getAllSalesRecords(int(year))
        
        return result

@salesPipelineView.route("/dashboard/salespipeline/2024/add", methods=['GET','POST'])
@auth.token_auth("/dashboard/salespipeline/2024/add")
def addToSalesPipeline():
    #to add the data, send the dropdown data from mongodb
    if request.method == 'GET':
        result = getDropDownData()
        return result
    
    #when data comes from frontend
    if request.method == 'POST':
        result = addSalesRecord(request.json)
        # print(result)
        return result

@salesPipelineView.route("/dashboard/salespipeline/2024/edit", methods=['GET','PUT'])
@auth.token_auth("/dashboard/salespipeline/2024/edit")
def editSalesPipeline():
    #to add the data, send the dropdown data from mongodb
    if request.method == 'GET':
        result = getDropDownData()
        return result
    if request.method == 'PUT':
        result = editSalesRecord(request.json)
        return result

@salesPipelineView.route("/dashboard/salespipeline/2024/delete", methods=['GET','DELETE'])
@auth.token_auth("/dashboard/salespipeline/2024/delete")
def deleteSalesPipeline():
    if request.method == 'DELETE':
        result = deleteSalesRecord(request.json)
        return result

@salesPipelineView.route("/dashboard/salespipeline/excel", methods=['GET'])
@auth.token_auth("/dashboard/salespipeline/excel")
def sendExcel():
    if request.method == "GET":
        return downloadExcel()
    


