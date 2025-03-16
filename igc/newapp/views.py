from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from services.CoinSearchHandler import CoinSearchHandler
from services.Helper import Helper

import json
import csv

import pandas as pd


coinSearchHandler = CoinSearchHandler()
helper = Helper("newapp/ressources/mintMap.csv") 

#mintMap_df = pd.read_csv("newapp/ressources/mintMap.csv")
#mintMap_df = mintMap_df.set_index('mint')
#mintMap = mintMap_df['mintLabel'].to_dict()

mintMap = helper.get_mint_map() 


def index(request):
	"""
	Renders the main index page of the web application.

	Parameters:
		request: The HTTP request object.

	Returns:
		HttpResponse: The rendered index page.
	
	Author: Danilo Pantic
	"""
	template = loader.get_template('index.html')

	return HttpResponse(template.render())


def convertId(id_str):
	"""
	Converts an ID string to a usable format.

	Parameters:
		id_str (str): The ID string to convert.

	Returns:
		str: The converted ID.
	
	Author: Danilo Pantic
	"""
	if "coin_id=" in id_str:
		return id_str.split("coin_id=")[1]
	else:
		return id_str


def download_search_results(request):
	"""
	Handles the downloading of search results in various formats.

	Parameters:
		request: The HTTP request object.

	Returns:
		HttpResponse: A response object with the file download or an error message.
	
	Author: Mohammed Sayed Mahmod
	"""
	if request.method == "POST":
		fileType = request.POST["fileType"]
		searchType = request.POST["searchType"]
		query = request.POST["q"]

		results = coinSearchHandler.executeQuery(query)
		
		if fileType == "csv":
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = f'attachment; filename="{searchType}_search_results.csv"'

			writer = csv.writer(response)
			writer.writerow([
				"Type", "URL", "Thumbnail Obverse", "Thumbnail Reverse", "ID", 
				"Weight", "Obverse Description", "Reverse Description", 
				"Date", "Max Diameter", "Location", "Region"
			])

			for row in results:
				writer.writerow([
					searchType,
					str(row.url) if row.url else "",
					str(row.thumbnailObverse) if row.thumbnailObverse else "static/no_image.jpg",
					str(row.thumbnailReverse) if row.thumbnailReverse else "static/no_image.jpg",
					convertId(str(row.id)),
					f"{row.weight} g" if row.weight else "",
					str(row.descriptionObverse) if row.descriptionObverse else "",
					str(row.descriptionReverse) if row.descriptionReverse else "",
					str(row.date) if row.date else "",
					f"{row.maxDiameter} mm" if row.maxDiameter else "",
					mintMap.get(str(row.mint), "") if row.mint else "",
					""
				])

			return response
		else:
			return JsonResponse({"error": "Unsupported fileType"}, status=400)
	else:
		return HttpResponse(status=405)


@csrf_exempt
def log(request):
	"""
	Endpoint for logging events from the front end.

	Parameters:
		request: The HTTP request object.

	Returns:
		JsonResponse: A response indicating success or failure of the log operation.
	
	Author: Mohammed Sayed Mahmod
	"""
	if request.method == 'POST':
		try:
			data = json.loads(request.body.decode('utf-8'))
			uuid = data.get('uuid')
			design = data.get('design')
			event = data.get('event')
			log_data = data.get('data')
			timestamp = data.get('timestamp')

			with open("newapp/logs/log.csv", "a+", newline='') as f:
				writer = csv.writer(f)
				writer.writerow([uuid, design, event, log_data, timestamp])

			return JsonResponse({"success": True, "message": "Log saved"})
		except json.JSONDecodeError:
			return JsonResponse({"success": False, "message": "Invalid JSON"})
		except Exception as e:
			return JsonResponse({"success": False, "message": str(e)})
	else:
		return JsonResponse({"success": False, "message": "Only POST method allowed"})


@csrf_exempt
def callback(request):
	"""
	The main callback endpoint for handling various actions from the frontend.

	Parameters:
		request: The HTTP request object.

	Returns:
		JsonResponse: A response object with the result of the action or an error message.
	
	Author: Mohammed Sayed Mahmod
	"""
	response = {"success": False}
	if request.method == "POST":
		if "action" in request.POST:
			a = request.POST["action"]
			

			#------------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------#
			# Now uses the new getRecommendationsSubObj and getRecommendationsPredicate functions,
			# which generate the recommandations based on the Database instead of CSV Files  
			if  "getRecommendations" in a:
				
				#-- NEW --
				subj_uri = request.POST["subj_uri"]
				obj_uri = request.POST["obj_uri"]
				side = request.POST["side"]
				#-- NEW --

				# differs now between recommendations of subject, objects and recommendations of predicates
				if a == "getRecommendationsPredicate":

					input = request.POST["q"]
					json_result = coinSearchHandler.getRecommendationsPredicate(subj_uri, obj_uri, input, side)
					response["result"] = json_result
					response["success"] = True
				
				elif a == "getRecommendationsSubObj":
					
					#-- NEW --
					pred_uri = request.POST["pred_uri"]
					search_type = request.POST["search_type"]
					is_subject = request.POST["is_subject"]
					#-- NEW --

					# Defines different variables for q (user input) based on search type
					# Reason: Unlike standart search, for the hierarchy search there are two inputs the tag of the search field,
					# upon which the hierachy search is performed and the text input which is used to filter the results.
					if search_type == "standard":
						input = request.POST["q"]
					else:
						filter = request.POST["q"]

					# Performs the right search based on the search type
					if search_type == "standard":
						json_result = coinSearchHandler.getRecommendationsSubObj(subj_uri,pred_uri,obj_uri, is_subject, input, side)
					elif search_type == "hierarchy-generalise-simple":
						json_result = coinSearchHandler.getSimpleGeneraliseRecommendationsOfCurrentSubObj(subj_uri, pred_uri, obj_uri, is_subject, side, filter)
					elif search_type == "hierarchy-specialise-simple":
						json_result = coinSearchHandler.getSimpleSpecializRecommendationsOfCurrentSubObj(subj_uri, pred_uri, obj_uri, is_subject, side, filter)
					elif search_type == "hierarchy-generalise-absolute":
						json_result = coinSearchHandler.getAbsoluteGeneraliseRecommendationsOfCurrentSubObj(subj_uri, pred_uri, obj_uri, is_subject, side, filter)
					elif search_type == "hierarchy-specialise-absolute":
						json_result = coinSearchHandler.getAbsoluteSpecializRecommendationsOfCurrentSubObj(subj_uri, pred_uri, obj_uri, is_subject, side, filter)
					elif search_type == "hierarchy-equivalent":
						json_result = coinSearchHandler.getEquivalentRecommendationsToCurrentSubObj(subj_uri, pred_uri, obj_uri, is_subject, side, filter)

					response["result"] = json_result
					response["success"] = True
			#Checks if recommendations are available for different search types
			elif "RecommendationsAvailable" in a:
				#Checks if specialise recommendations are available
				if a == "areSpecialiseRecommendationsAvailable":
					filter = request.POST["q"]
					subj_uri = request.POST["subj_uri"]
					pred_uri = request.POST["pred_uri"]
					obj_uri = request.POST["obj_uri"]
					is_subject = request.POST["is_subject"]
					side = request.POST["side"]
					json_result = coinSearchHandler.areSpecialiseRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, filter, side)
				#Checks if generalise recommendations are available
				elif a == "areGeneraliseRecommendationsAvailable":
					filter = request.POST["q"]
					subj_uri = request.POST["subj_uri"]
					pred_uri = request.POST["pred_uri"]
					obj_uri = request.POST["obj_uri"]
					is_subject = request.POST["is_subject"]
					side = request.POST["side"]
					json_result = coinSearchHandler.areGeneraliseRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, filter, side)
				#Checks if equivalent recommendations are available	
				elif a == "areEquivalentRecommendationsAvailable":
					filter = request.POST["q"]
					subj_uri = request.POST["subj_uri"]
					pred_uri = request.POST["pred_uri"]
					obj_uri = request.POST["obj_uri"]
					is_subject = request.POST["is_subject"]
					side = request.POST["side"]
					json_result = coinSearchHandler.areEquivalentRecommendationsOfCurrentTagAvailable(subj_uri, pred_uri, obj_uri, is_subject, filter, side)
				#Checks if recommendations for predicate and objects are available for current subject (by Steven Nowak)
				elif a == "areRecommendationsAvailable":
					subj_uri = request.POST["subj_uri"]
					side = request.POST["side"]
					json_result = coinSearchHandler.areRecommendationsAvailable(subj_uri, side)

				response["result"] = json_result
				response["success"] = True
			#---------------------------------------------------------------------------------- (-END-) NEW by Nico Lambert --------------------------------#

			elif a == "generateQuery":
				coins = json.loads(request.POST["coins"])
				relationString = request.POST["relationString"]
				searchType = request.POST["searchType"]
				response["result"] = coinSearchHandler.generateQuery(coins, relationString, searchType)
				response["success"] = True
			elif a == "searchCoin":

				searchType = request.POST["searchType"]
				results = coinSearchHandler.executeQuery(request.POST["q"])

				result = []
				
				for row in results:
					category = row.type if searchType == "NumismaticObject" else "TYPE" if searchType == "TypeSeriesItem" else None

					result_item = {
						"type": searchType,
						"url": str(row.url) if row.url else None,
						"thumbnailObverse": str(row.thumbnailObverse) if row.thumbnailObverse else "static/no_image.jpg",
						"thumbnailReverse": str(row.thumbnailReverse) if row.thumbnailReverse else "static/no_image.jpg",
						"descriptionObverse": str(row.descriptionObverse) if row.descriptionObverse else None,
						"descriptionReverse": str(row.descriptionReverse) if row.descriptionReverse else None,
						"date": str(row.date) if row.date else None,
						"maxDiameter": float(row.maxDiameter) if row.maxDiameter else None,
						"id": convertId(row.id),
						"category": category,
						"weight": float(row.weight) if row.weight else None,
						"location": mintMap.get(str(row.mint), None) if searchType == "NumismaticObject" else "TYPE",
						"region": None if searchType == "NumismaticObject" else convertId(row.id)
					}

					result.append(result_item)

				response["success"] = True
				response["result"] = result
				response["length"] = len(results)
			elif a == "download":
				return download_search_results(request)

	return JsonResponse(response, safe=False)