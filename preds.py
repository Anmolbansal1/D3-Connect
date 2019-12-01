def age_sim(user_age, rec_age):
	sim = abs(40-abs(user_age-rec_age))/40
	return sim**3

def occ_sim(user_occ, rec_occ):
	if user_occ == rec_occ:
		return 1
	else:
		return 0

def interest_sim(user_int, rec_int):
	user_int = user_int.split(',')
	rec_int = rec_int.split(',')
	cnt = 0
	m = len(user_int)
	for df in user_int:
		for dg in rec_int:
	  		if df == dg:
				cnt += 1
	if len(rec_int) > m:
		m = len(rec_int)
	return (cnt/m)


def location_sim(geolocator, user_loc, rec_loc):
	#location in format City,Country
	user_loc = [user_loc, 'India']
	rec_loc = [rec_loc, 'India']
	loc1 = geolocator.geocode(user_loc)
	loc2 = geolocator.geocode(rec_loc)
	lon1 = loc1.longitude
	lon2 = loc2.longitude
	lat1 = loc1.latitude
	lat2 = loc2.latitude
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	dist = 6371 * (acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)))
	return (1-dist/19994)**10
