#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys, datetime, os, re
import argparse, traceback, time, datetime
'''
Simple twitter bot script

needs config file contiaining usernames and api keys in the following format:
	@<user_1>
	CONSUMER_KEY	<key>
	CONSUMER_SECRET	<secret>
	ACCESS_KEY	<key>
	ACCESS_SECRET	<secret>
	@<user_2>
	CONSUMER_KEY	<key>
	CONSUMER_SECRET	<secret>
	ACCESS_KEY	<key>
	ACCESS_SECRET	<secret>
'''

def main():
    parser = argparse.ArgumentParser()
    reqd = parser.add_argument_group('required arguments')
    reqd.add_argument('-c','--config',action='store',dest='con',help='Path to config file',required=True)
    reqd.add_argument('-v', '--victim',action='store',dest='vic',help='Username to torment',required=True)
    args = parser.parse_args()

    keys = get_keys(args.con)
    
    try:
        run(get_twitter_api(keys), args.vic)
    except tweepy.TweepError as e:
        print(str(e))
        if e.api_code == 88: # rate limited
            print("Rate limited")
        elif e.api_code == 64: # bot account suspended
            print("Suspended")
        elif e.api_code == 136: # bot account is blocked from responding to the victim
            print("Blocked")
    except KeyboardInterrupt:
        print("Killed")
            
    sys.exit(0)

def run(apis, victim):
    '''
    Run the campaign

    Doesn't work as intended. If user is blocked, the bot is able to tweet in reply to any status update by
    the victim, but the tweets cannot be seen by anyone

    It was worth a shot though

    @param list twitter apis
    @return none
    '''
    tweet_ids = []
    for api in apis:
        #print("here")
        if not api.verify_credentials():
            print("ERROR: Twitter AUTH failure for: "+api.get_user(screen_name))
            raise tweepy.TweepError
        print("@"+api.me().screen_name+" authenticated and connected")

    spotter = apis[0]
    stalker = apis[1]
    i = 0
    while True:
        # check vicitm's timeline for latest tweet
        for tweet in spotter.user_timeline(screen_name=victim, count=1):
            # check that latest tweet is < 5 min old and hasn't already been responded to
            if (time.time() - (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds() < 300) and (tweet.id not in tweet_ids):
                tweet_ids.append(tweet.id)
                # str(i) is concatenated to the string to prevent twitter's duplicate status checks
                stalker.update_status('@'+victim+ ' sup '+str(i), in_reply_to_status=tweet.id) # have stalker reply to tweet found by spotter
                # api.update_with_media('victims/media/113047940.jpg','@' + victim_list[current_user]+' pls clap', in_reply_to_status_id = tweet.id)
                i += 1
                print("Responded to "+victim)
            time.sleep(5)
    
def get_keys(fp):
    '''
    Get user api keys from config file

    @param string file path
    @return list (user, api_key_list)
    '''
    keys = []
    user_keys = []
    with open(fp,'r') as f:
        keys = f.readlines()

    for i in range(0, len(keys)):
        if '@' in keys[i]:
            j = i + 1
            tmp = []
            for j in range(j, j+4):
                tmp.append(keys[j])

            user_keys.append((keys[i], tmp))

    return user_keys

def get_twitter_api(api_keys):
    '''
    Returns a list of authenticated twitter apis

    api_keys[0] is the user name
    api_keys[1] is a list of the user's api keys

    @param api_key_list
    @return list of twitter apis
    '''
    tweepy_apis = []
    for i in api_keys:
        tmp = i[1]
        auth = tweepy.OAuthHandler(re.sub('[^A-Za-z0-9\-]+','',tmp[0].split('\t')[1]), re.sub('[^A-Za-z0-9\-]+','',tmp[1].split('\t')[1]))
        auth.set_access_token(re.sub('[^A-Za-z0-9\-]+','',tmp[2].split('\t')[1]), re.sub('[^A-Za-z0-9\-]+','',tmp[3].split('\t')[1]))
        tweepy_apis.append(tweepy.API(auth))

    return tweepy_apis


if __name__ == "__main__":
    main()
