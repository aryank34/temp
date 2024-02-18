from flask import Blueprint, request, make_response
from ..loginAuth.tokenAuth import tokenAuth
from .dbConnection import addSalesRecord, getAllSalesRecords, getDropDownData, editSalesRecord, deleteSalesRecord, getAllYears 

auth = tokenAuth()

salesPipelineView = Blueprint('salesPipelineView',__name__)

@salesPipelineView.route("/dashboard/salespipeline", methods=['GET'])
@auth.token_auth("/dashboard/salespipeline")
def getYears():
    if request.method == 'GET':
        return getAllYears()

@salesPipelineView.route("/dashboard/salespipeline/<year>", methods=['GET'])
@auth.token_auth("/dashboard/salespipeline/<year>")
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
