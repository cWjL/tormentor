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
b_prefix = ""
g_prefix = ""

def main():
    parser = argparse.ArgumentParser()
    reqd = parser.add_argument_group('required arguments')
    reqd.add_argument('-c','--config',action='store',dest='con',help='Path to config file',required=True)
    reqd.add_argument('-v', '--victim',action='store',dest='vic',help='Path to username file',required=True)
    args = parser.parse_args()
    
    global b_prefix
    global g_prefix
    
    try:
        import colorama
        from colorama import Fore, Style
        b_prefix = "["+Fore.RED+" FAIL "+Style.RESET_ALL+"] "
        g_prefix = "["+Fore.GREEN+"  OK  "+Style.RESET_ALL+"] "
    except ImportError:
        b_prefix = "[ FAIL ] "
        g_prefix = "[  OK  ] "
        
    keys = _get_keys(args.con)
    
    try:
        _run(_get_twitter_api(keys), _get_victims(args.vic))
    except tweepy.TweepError as e:
        if e.api_code == 88: # rate limited
            print(b_prefix+"[Rate limited] "+str(e))
        elif e.api_code == 64: # bot account suspended
            print(b_prefix+"[Suspended] "+str(e))
        elif e.api_code == 136: # bot account is blocked from responding to the victim
            print(b_prefix+"[Blocked] "+str(e))
        else:
            print(b_prefix+"[Error] "+str(e))
    except KeyboardInterrupt:
        print(g_prefix+"User interrupt")
            
    sys.exit(0)

def _run(apis, victim):
    '''
    Run the campaign

    Doesn't work as intended. If user is blocked, the bot is able to tweet in reply to any status update by
    the victim, but the tweets cannot be seen by anyone

    It was worth a shot though

    @param list twitter apis
    @param list victims
    @return none
    '''
    global b_prefix
    global g_prefix
    
    tweet_ids = []
    tweet_text = []
    tweet_media = []
    
    for api in apis:

        if not api.verify_credentials():
            print(b_prefix+"ERROR: Twitter AUTH failure for: "+api.get_user(screen_name))
            raise tweepy.TweepError
        print(g_prefix+"@"+api.me().screen_name+" authenticated and connected")
        res = input(g_prefix+"Give me the path to "+api.me().screen_name+" wordlist: ")
        tweet_text.append((api.me.screen_name, _get_tweet_text(res))) # Get tweet text for replies
        res = input(g_prefix+"Give me the path to "+api.me().screen_name+" media files, or <ENTER> for none: ")
        if res is not None:
            tweet_media.append((api.me.screen_name, _get_media_files(res))) # Get media files for replies
        
    while True:
        for tweet in spotter.user_timeline(screen_name=victim, count=1):
            # check that latest tweet is < 5 min old and hasn't already been responded to
            if (time.time() - (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds() < 300) and (tweet.id not in tweet_ids):
                tweet_ids.append(tweet.id)

                stalker.update_status('@'+victim+ ' sup '+str(i), in_reply_to_status=tweet.id) # have stalker reply to tweet found by spotter
                
                i += 1
                print("Responded to "+victim)
            time.sleep(5)

def _get_tweet_text(fp):
    '''
    Get text file of tweet text

    @param file path
    @return list of tweet text
    '''
    text = []
    with open(fp,'r') as twt:
        text = twt.readlines()
    return text

def _get_media_files(fp):
    '''
    Get media files from a directory

    @param file path
    @return list of media files
    '''
    files = []
    for file in os.listdir(fp):
        files.append(os.path.join(fp,file))

    return files

def _update_no_media(tweeter, tweet, say_this):
    '''
    Update twitter stat with text only

    @param api of user sending the tweet
    @param api of user receiving tweet
    @param string of what to tweet
    '''
    tweeter.update_status('@'+tweet.screen_name+' '+say_this, in_reply_to_status=tweet.id)

def _update_w_media(tweeter, tweet, say_this, with_this):
    '''
    Update twitter stat with text and media

    @param api of user sending the tweet
    @param api of user receiving tweet
    @param string of what to say
    @param string file path to media
    '''
    tweeter.update_with_media(with_this,'@'+tweet.screen_name+' '+say_this, in_reply_to_status_id = tweet.id)

def _get_victims(fp):
    '''
    Get list of users to torment

    @param string file path
    @return list users
    '''
    torment = []
    with open(fp,'r') as in_file:
        torment = in_file.readlines()
    return torment
    
def _get_keys(fp):
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

def _get_twitter_api(api_keys):
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
