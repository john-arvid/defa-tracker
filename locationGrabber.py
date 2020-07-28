import requests, re, webbrowser, math, datetime, time
from authentication import *

def vincenty_inverse(point1, point2, miles=False):
	
	# short-circuit coincident points
	if point1[0] == point2[0] and point1[1] == point2[1]:
		return 0.0
	
	U1 = math.atan((1 - f) * math.tan(math.radians(point1[0])))
	U2 = math.atan((1 - f) * math.tan(math.radians(point2[0])))
	L = math.radians(point2[1] - point1[1])
	Lambda = L
	
	sinU1 = math.sin(U1)
	cosU1 = math.cos(U1)
	sinU2 = math.sin(U2)
	cosU2 = math.cos(U2)
	
	for __ in range(MAX_ITERATIONS):
		sinLambda = math.sin(Lambda)
		cosLambda = math.cos(Lambda)
		sinSigma = math.sqrt((cosU2 * sinLambda) ** 2 +
			(cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
		
		if sinSigma == 0:
			return 0.0  # coincident points
		cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
		sigma = math.atan2(sinSigma, cosSigma)
		sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
		cosSqAlpha = 1 - sinAlpha ** 2
		try:
			cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
		except ZeroDivisionError:
			cos2SigmaM = 0
			C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
			LambdaPrev = Lambda
			Lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinSigma *
				(cos2SigmaM + C * cosSigma *
				(-1 + 2 * cos2SigmaM ** 2)))
			
			if abs(Lambda - LambdaPrev) < CONVERGENCE_THRESHOLD:
				break  # successful convergence
			else:
				return None  # failure to converge
	
	uSq = cosSqAlpha * (a ** 2 - b ** 2) / (b ** 2)
	A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
	B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
	deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma *
		(-1 + 2 * cos2SigmaM ** 2) - B / 6 * cos2SigmaM *
		(-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
	s = b * A * (sigma - deltaSigma)
	
	s /= 1000  # meters to kilometers
	if miles:
		s *= MILES_PER_KILOMETER  # kilometers to miles
	
	return round(s, 6)

def calculate_initial_compass_bearing(pointA, pointB):
    """
	Credit: https://gist.github.com/jeromer/2005586
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def send_error(error_text):
	print(error_text)
	time.sleep(30)
	return

#WGS 84
a = 6378137  # meters
f = 1 / 298.257223563
b = 6356752.314245  # meters; b = (1 - f)a

MILES_PER_KILOMETER = 0.621371

MAX_ITERATIONS = 200
CONVERGENCE_THRESHOLD = 1e-12  # .000,000,000,001

latitude = 0
longitude = 0
last_longitude = 0
last_latitude = 0
last_time = 0
this_time = 0
error = 0



cookie = dict(JSESSIONID='xxx')
headers = {'Content-Type': 'application/json', 'User-Agent': 'DEFALink-iOS/6.6.23'}
regex = r"\d+(?=,\"type\":43})"

while (True):

	# Reset error state
	error = 0

	# Set time variables
	if (this_time != 0):
		last_time = this_time

	this_time = datetime.datetime.now()

	# Set variable so we have two different points
	if (longitude != 0):
		last_longitude = longitude
		last_latitude = latitude
		#if (something something): error = 1

	# Get the response from defa server
	try:
		response = requests.post(url, headers=headers, cookies=cookie, json=payload)
	except:
		error = 1
		error_text = this_time.strftime("%Y.%m.%d %H:%M:%S ") + "Something wrong with defa url"
		send_error(error_text)
		response.status_code == 420

	# Get the session id the first time or when the session id has changed
	if (longitude == 0 or response.status_code != 200) and not error:
		headers2 = {'Content-Type':'application/json','User-Agent':'DEFALink-iOS/6.6.23'}
		payload2 = {"username":username,"password":password,"clientVer":"6.6.23","clientType":"defalink_ios"}
		url2 = 'https://api.mydefa.com/link/LoginService.svc/login'
		regex2 = r"(?<=JSESSIONID=)[A-Z0-9]*"

		try:
			response2 = requests.post(url2, headers=headers2, json=payload2)
		except:
			error = 1
			error_text = this_time.strftime("%Y.%m.%d %H:%M:%S ") + "Something wrong with defa url"
			send_error(error_text)
		
		authcookie = str(response2.headers)
		#print(authcookie)
		matches = re.findall(regex2, authcookie)
		authcookie = matches[0]
		cookie = dict(JSESSIONID=authcookie)

		try:
			response = requests.post(url, headers=headers, cookies=cookie, json=payload)
		except:
			error = 1
			error_text = this_time.strftime("%Y.%m.%d %H:%M:%S ") + "Something wrong with defa url"
			send_error(error_text)
			response.status_code == 420

	#print(response.status_code)

	text = response.text

	#print(text)
	if (not error):

		try:
			matches = re.findall(regex, text)

		except:
			error_text = this_time.strftime("%Y.%m.%d %H:%M:%S ") + "No JSSESION found in the server response"
			send_error(error_text)
			print(text)
			error = 1

		try:
			latitude = matches[0]
			longitude = matches[1]
		except:
			error_text = this_time.strftime("%Y.%m.%d %H:%M:%S ") + "Lat and long not found"
			send_error(error_text)
			print(text)
			error = 1

		temp = abs(int(latitude)) % 10000000
		latitude = str(int(latitude) // 10000000) + "." + str(temp)
		latitude = float(latitude)

		temp = abs(int(longitude)) % 10000000
		longitude = str(int(longitude) // 10000000) + "." + str(temp)
		longitude = float(longitude)

		latSeconds = latitude * 3600
		latDegrees = latSeconds / 3600
		latSeconds = abs(latSeconds % 3600)
		latMinutes = latSeconds / 60
		latSeconds %= 60
		latSeconds = round(latSeconds,1)
		latMinutes = int(latMinutes)
		latDegrees = int(latDegrees)

		longSeconds = longitude * 3600
		longDegrees = longSeconds / 3600
		longSeconds = abs(longSeconds % 3600)
		longMinutes = longSeconds / 60
		longSeconds %= 60
		longSeconds = round(longSeconds,1)
		longMinutes = int(longMinutes)
		longDegrees = int(longDegrees)

	#mapURL = ("https://www.google.com/maps/place/" + str(latDegrees) + "%C2%B0" + str(latMinutes) + "'" + str(latSeconds) + "%22" + 'N+' + str(longDegrees) + "%C2%B0" + str(longMinutes) + "'" + str(longSeconds) + '%22' + 'E/@' + str(latitude) + "," + str(longitude) + ",17z")

	#webbrowser.open_new(mapURL)

	if (last_latitude != 0 and not error):
		last_point = [last_latitude,last_longitude]
		this_point = [latitude, longitude]
		distance = vincenty_inverse(last_point,this_point)
		time_difference = this_time - last_time
		# This function needs tuple, but I am using arrays, so I convert them before sending it
		bearing = calculate_initial_compass_bearing(tuple(last_point), tuple(this_point))
		#print(bearing)
		speed = round(((distance/time_difference.total_seconds())*3600)/1.852,2)
		unixtime = datetime.datetime.utcnow().timestamp()
		try:
			response3 = requests.post(f"http://192.168.1.20:18582/?id=48945893489&lat={latitude}&lon={longitude}&timestamp={this_time}&speed={speed}&bearing={bearing}")
		except:
			error_text = this_time.strftime("%Y.%m.%d %H:%M:%S ") + "Traccar not available"
			send_error(error_text)
			print(response3.status_code)
			print(response3.text)
	#print(response.status_code)


