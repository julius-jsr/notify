


import base64
import cgi
import Cookie
import email.utils
import os
import webapp2
import jinja2
import hmac
import re
import urlparse
import hashlib
import urllib2
import json
import logging
import time
import urllib
import exceptions
import requests
from HTMLParser import HTMLParser
from xml.dom import minidom
from datetime import date
from datetime import timedelta
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import urlfetch


FACEBOOK_APP_ID = "229148887269452"
FACEBOOK_APP_SECRET = "6e83b9196f1b621fd77dad02b2e1c8c9"

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))
        
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def get_current_user(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                self._current_user = User.get_by_key_name(user_id)
        return self._current_user
    def get_current_user_id(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                return user_id
            else:
                return None
        return None




    


class User(db.Model):
    id = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    nickname = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    parse_id=db.StringProperty(required=True)
    channels_owned=db.StringListProperty ()
    channels_subscribed=db.StringListProperty()

class channel(db.Model):
    id = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    admin_fb_id = db.StringProperty(required=True)


class del_all(BaseHandler):
    def get(self):
       
        q = db.GqlQuery("SELECT * FROM User")
        results = q.fetch(1000)
        db.delete(results)
        self.write("done")

class ChannelCheck(BaseHandler):
    def post(self):
        channel_id=self.request.get("channel_id")
        

        z=db.GqlQuery("SELECT * FROM channel WHERE id = :1",channel_id)

        flag=0
        for x in z:
            flag=1
            break
        if flag==0:
            self.write(json.dumps({
				'status' : 'available'
				}))
        else:
            self.write(json.dumps({
				'status' : 'na'
				}))


class ChannelSearch_by_name(BaseHandler):
    def post(self):
        keyword=self.request.get("keyword")
        z=db.GqlQuery("SELECT * FROM channel")
        lis=[]
        for x in z:
            if keyword in x.name:
                entry={}
                entry["id"]=x.id
                entry["name"]=x.name
                lis.append(entry)

    
        self.write(json.dumps({
            'channels' : lis
            }))

class ChannelSearch_by_id(BaseHandler):
    def post(self):
        keyword=self.request.get("keyword")

        z=db.GqlQuery("SELECT * FROM channel WHERE id = :1",keyword)
        lis=[]
        for x in z:
            entry={}
            entry["id"]=x.id
            entry["name"]=x.name
            lis.append(entry)

    
        self.write(json.dumps({
            'channels' : lis
            }))

    def get(self):
        keyword=self.request.get("keyword")
        z=db.GqlQuery("SELECT * FROM channel WHERE id = :1",keyword)
        lis=[]
        for x in z:
            entry={}
            entry["id"]=x.id
            entry["name"]=x.name
            lis.append(entry)

    
        self.write(json.dumps({
            'channels' : lis
            }))

    
    
        
    

class ChannelSubscribe(BaseHandler):
    def post(self):
        
        admin_fb_id=self.request.get("admin_fb_id")
        channel_id=self.request.get("channel_id")

        

        z=db.GqlQuery("SELECT * FROM User WHERE id = :1",admin_fb_id)

        for x in z:
            channels_subscribed=x.channels_subscribed
            channels_subscribed.append(channel_id)
            w=User(key_name=x.id,id=x.id,name=x.name,nickname=x.nickname,email=x.email,
                   profile_url=x.profile_url,access_token=x.access_token,
                   parse_id=x.parse_id,channels_owned=x.channels_owned,
                   channels_subscribed=channels_subscribed
                   )
            w.put()
        
        self.write(json.dumps({
            'status' : 'done'
            }))



    
class ChannelCreate(BaseHandler):
    def post(self):
        channel_name=self.request.get("channel_name")
        admin_fb_id=self.request.get("admin_fb_id")
        channel_id=self.request.get("channel_id")

        ww=channel(id=channel_id,
                   admin_fb_id=admin_fb_id,
                   name=channel_name
                   )
        ww.put()

        z=db.GqlQuery("SELECT * FROM User WHERE id = :1",admin_fb_id)

        for x in z:
            channels_owned=x.channels_owned
            channels_owned.append(channel_id)
            w=User(key_name=x.id,id=x.id,name=x.name,nickname=x.nickname,email=x.email,
                   profile_url=x.profile_url,access_token=x.access_token,
                   parse_id=x.parse_id,channels_owned=channels_owned,
                   channels_subscribed=x.channels_subscribed
                   )
            w.put()
        
        self.write(json.dumps({
            'status' : 'done'
            }))


class LoginHandler(BaseHandler):
    def post(self):

        verification_code = self.request.get("code")
        url = self.request.get("continue")
        parse_id= self.request.get("parse_id")
        #args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
        #self.redirect(
         #   "https://graph.facebook.com/oauth/authorize?" +
          #  urllib.urlencode(args))


        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url, scope='email publish_actions')
        if self.request.get("token"):
            access_token=self.request.get("token")
            # Download the user profile and cache a local instance of the
            # basic profile info
            profile = json.load(urllib.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))
            print profile.keys()
            user = User(key_name=str(profile["id"]), id=str(profile["id"]),
                        name=profile["name"], nickname=profile["username"],
                        email=profile["email"], access_token=access_token,
                        profile_url=profile["link"],parse_id=parse_id)
            user.put()
            
            self.write(json.dumps({
				'status' : 'DONE'
				}))
        else:
            self.write(json.dumps({
				'status' : 'NOT DONE'
				
				}))
    def get(self):

        verification_code = self.request.get("code")
        url = self.request.get("continue")
        parse_id= self.request.get("parse_id")
        #args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
        #self.redirect(
         #   "https://graph.facebook.com/oauth/authorize?" +
          #  urllib.urlencode(args))


        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url, scope='email publish_actions')
        if self.request.get("token"):
            access_token=self.request.get("token")
            # Download the user profile and cache a local instance of the
            # basic profile info
            profile = json.load(urllib.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))
            print profile.keys()
            user = User(key_name=str(profile["id"]), id=str(profile["id"]),
                        name=profile["name"], nickname=profile["username"],
                        email=profile["email"], access_token=access_token,
                        profile_url=profile["link"],parse_id=parse_id)
            user.put()
            
            self.write(json.dumps({
				'status' : 'DONE'
				}))
        else:
            self.write(json.dumps({
				'status' : 'NOT DONE'
				
				}))

app = webapp2.WSGIApplication([('/login', LoginHandler),
                               ('/check_channel', ChannelCheck),
                               ('/create_channel',ChannelCreate),
                               ('/channel_search_id',ChannelSearch_by_id),
                               ('/channel_search_name',ChannelSearch_by_name),
                               ('/channel_subscribe',ChannelSubscribe),
                               ('/del',del_all)
                               ])
