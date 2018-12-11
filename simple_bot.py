#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy, time, sys, datetime, os, re
import argparse, traceback, time, datetime
from threading import Thread
import traceback
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
        thread_list = _get_threads(_get_twitter_api(keys), _get_victims(args.vic))
        print(g_prefix+"Starting bot threads")
        for bot in thread_list:
            bot.start()
        print(g_prefix+"Bots running")
        for bot in thread_list:
            bot.join()
        print(g_prefix+"Bots done")
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
        print('\n'+g_prefix+"User interrupt")
    except Exception as e:
        print(b_prefix+"Error: "+str(e))
        traceback.print_exc()
            
    sys.exit(0)

def _get_threads(apis, victim):
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
    bot_threads = []
    res = ""
    for api in apis:

        if not api.verify_credentials():
            print(b_prefix+"ERROR: Twitter AUTH failure for: "+api.get_user(screen_name))
            raise tweepy.TweepError
        print(g_prefix+"@"+api.me().screen_name+" authenticated and connected")
        res = input(g_prefix+'Give me the path to '+api.me().screen_name+' wordlist: ')
        tweet_text.append((api.me().screen_name, _get_tweet_text(res))) # Get tweet text for replies
        res = ""
        res = input(g_prefix+"Give me the path to "+api.me().screen_name+" media files, or <ENTER> for none: ")
        if res != "":
            tweet_media.append((api.me().screen_name, _get_media_files(res))) # Get media files for replies
        else:
            tweet_media = None

    for api in apis: # Select victim and set up threads
        i = 0
        who = True
        print('\n')
        for vic in victim:
            print("\t["+str(i)+"] "+vic)
            i += 1

        while who:
            res = input(g_prefix+"Who should "+api.me().screen_name+" torment? ")
            if int(res) >= 0 and int(res) < len(victim):
                who = False
            else:
                print(b_prefix+"Incorrect selection")
        bot = Soldier(api, tweet_text, victim[int(res)], tweet_media)
        bot.daemon = True
        bot_threads.append(bot)
    return bot_threads

def _get_tweet_text(fp):
    '''
    Get text file of tweet text

    @param file path
    @return list of tweet text
    '''
    text = []
    with open(os.path.abspath(fp),'r') as twt:
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

class Soldier(Thread):
    '''
    Bot thread
    '''
    def __init__(self, twatter_api, text, victim, media=None):
        Thread.__init__(self)
        self.twatter_api = twatter_api
        self.media_list = media
        self.text_list = text
        self.victim = victim
        self.tweet_ids = []

    def run(self):
        while True:
            for tweet in self.twatter_api.user_timeline(screen_name=self.victim, count=1):
                if ((time.time() - (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds() < 300) and
                    (tweet.id not in self.tweet_ids)):
                    self.tweet_ids.append(tweet.id)
                    try:
                        if self.media_list is not None:
                            self._update_w_media(self.twatter_api, tweet, self.text_list.pop(0), self.media_list.pop(0))
                        else:
                            self._update_no_media(self.twatter_api, tweet, self.text_list.pop(0))
                    except IndexError:
                        break
                    except Exception:
                        break

    def _update_no_media(self, tweeter, tweet, say_this):
        '''
        Update twitter stat with text only
        
        @param api of user sending the tweet
        @param api of user receiving tweet
        @param string of what to tweet
        '''
        tweeter.update_status('@'+self.victim+' '+say_this, in_reply_to_status=tweet.id)

    def _update_w_media(self, tweeter, tweet, say_this, with_this):
        '''
        Update twitter stat with text and media
        
        @param api of user sending the tweet
        @param api of user receiving tweet
        @param string of what to say
        @param string file path to media
        '''
        tweeter.update_with_media(with_this,'@'+self.victim+' '+say_this, in_reply_to_status_id = tweet.id)


if __name__ == "__main__":
    main()
