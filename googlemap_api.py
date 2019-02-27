import requests, json

class Client():
	
	def __init__(self, api_key):
		self.api_key = api_key

	def get_latlng(self, address):
		BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key=AIzaSyAVyPc0WvJMmCvAplkkGODwj-1jUVoQKxU&language=zh-TW".format(address)
		res = json.loads(requests.get(BASE_URL).text)
		if "error_message" in res:
			error_message = res["error_message"]
			status = res["status"]
			print("status: {}, error_message: {}".format(status, error_message))
		else:
			results = res["results"][0]
			format_address = results["formatted_address"]
			lat = results["geometry"]["location"]["lat"]
			lng = results["geometry"]["location"]["lng"]
			return [format_address, [lat,lng]]

	def _latlng_codec(self, latlngs):
		result = ""
		for latlng in latlngs:
			str_latlng = str(latlng[0])+","+str(latlng[1])
			result = result + str_latlng+"|"
		result = result[:-1]
		return result

	def to_json(self, origin, destination):
		origin_codec = self._latlng_codec(origin)
		destination_codec = self._latlng_codec(destination)
		BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric"+\
					"&origins={}".format(origin_codec)+\
					"&destinations={}".format(destination_codec)+\
					"&key={}".format(self.api_key)
		res = json.loads(requests.get(BASE_URL).text)
		if "error_message" in res:
			error_message = res["error_message"]
			status = res["status"]
			print("status: {}, error_message: {}".format(status, error_message))
		else:
			return res

	def to_metrix(self, origin, destination, mode="distance"):
		tmp = self.to_json(origin, destination)
		# data structure : [[distance,duration],[distance,duration], ...]
		#				   [[distance,duration],[distance,duration], ...]
		#										...
		metrix = []
		for row in tmp["rows"]:
			return_list = []
			for element in row["elements"]:
				return_list.append(element[mode]["value"])
			metrix.append(return_list)

		return metrix
		
if __name__ == "__main__":
	#testing data
	api_key = "your_api_key"
	client = Client(api_key)
	origin_list = 	   [[25.0482323, 121.5393215], [25.0693178, 121.5880759], [25.0457061, 121.3658], [24.9855177, 121.2422759], [25.028047, 121.064149]] # origin 的經緯度，list，
	destination_list = [[25.0482323, 121.5393215], [25.0693178, 121.5880759], [25.0457061, 121.3658], [24.9855177, 121.2422759], [25.028047, 121.064149]]# destination 的經緯度，list，
	
	# 如果不設 mode 參數，預設是回來 distance
	distance_result = client.to_metrix(origin_list, destination_list, mode="distance")
	print(distance_result)

	duration_result = client.to_metrix(origin_list, destination_list, mode="duration")
	print(duration_result)

	latlng = client.get_latlng("台灣台北市大安區忠孝東路四段176號")
	print(latlng)
