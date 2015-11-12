import re
import sys
import json
from datetime import datetime
import time
import urllib2
import os


def friendly_time(dt, past_="ago", 
    future_ = "from now", 
    default = "just now"):
    """
    Returns string representing "time since"
    or "time until" e.g.
    3 days ago, 5 hours from now etc.
    """

    now = datetime.utcnow()
    if now > dt:
        diff = now - dt
        dt_is_past = True
    else:
        diff = dt - now
        dt_is_past = False

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:
        
        if period:
            return "%d %s %s" % (period, \
                singular if period == 1 else plural, \
                past_ if dt_is_past else future_)

    return default


def string_from_time(ti):
	return time.strftime('%Y-%m-%d %H:%M:%S',ti)

class Episode(object):
	def __init__(self,load):
		self.episode_number = load['episode_number']
		self.views = load['views']
		self.title = load['show']['title'].encode('ascii','ignore')
		self.show_id = load['show']['id']
		self.updated = load['created_at']
		self.synopsis = load['show']['synopsis']
		
	def get_relative_time(self):
		d = time.strptime(self.updated,'%Y-%m-%d %H:%M:%S')
		d2 = datetime.strptime(string_from_time(d),'%Y-%m-%d %H:%M:%S')
		return friendly_time(d2)


class Show(object):

	def __init__(self,load):
		self.id = load['id']
		self.title = load['title'].encode('ascii', 'ignore')

		if load['episode_count'] is not None:
			self.episode_count = int(load['episode_count'])

		self.synopsis = load['synopsis'].encode('ascii', 'ignore')
		self.views = load['views']

		#if load['status'] is not None:
		#	self.status = load['status']['name']

		self.episodes = []
