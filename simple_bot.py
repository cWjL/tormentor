#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy, time, sys, datetime, os, re
import argparse, traceback, time, datetime
import logging
from threading import Thread
'''
Simple twitter bot
'''
b_prefix = ""
g_prefix = ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o','--printout',action='store_true',dest='out',help='Print all activity to stdout')
    reqd = parser.add_argument_group('required arguments')
    reqd.add_argument('-c','--config',action='store',dest='con',help='Path to config file',required=True)
    reqd.add_argument('-v', '--victim',action='store',dest='vic',help='Path to username file',required=True)
    args = parser.parse_args()

    log = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S', filename='logs/torment.log', filemode='w')
    
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
        thread_list = _get_threads(_get_twitter_api(keys), _get_victims(args.vic), log, args.out)
        print(g_prefix+"Starting bot threads")
        for bot in thread_list:
            bot.start()
        print(g_prefix+"Bots running")
        for bot in thread_list:
            bot.join()

        print(g_prefix+"Bots done")
    except KeyboardInterrupt:
        print('\n'+g_prefix+"User interrupt")
    except Exception as e:
        print(b_prefix+"Error: "+str(e))
        print(b_prefix+str(traceback.print_exc()))
            
    sys.exit(0)

def _get_threads(apis, victim, log, print_out):
    '''
    Instantiate and return a list of bot objects

    @param list twitter apis
    @param list victims
    @return list of Soldier objects
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

    for api in apis:
        i = 0
        who = True
        print(g_prefix+"Select from list:")
        for vic in victim:
            print("\t["+str(i)+"] "+vic)
            i += 1
        # Select the victim
        while who:
            res = input(g_prefix+"Who should "+api.me().screen_name+" torment? ")
            if int(res) >= 0 and int(res) < len(victim):
                who = False
            else:
                print(b_prefix+"Incorrect selection")
        # Get instantiated bots
        for texts in tweet_text:
            if texts[0] == api.me().screen_name:
                if tweet_media is not None:
                    for media in tweet_media:
                        if media[0] == api.me().screen_name:
                            bot = Soldier(api, texts[1], victim[int(res)], log, print_out, media[1])
                else:
                    bot = Soldier(api, texts[1], victim[int(res)], log, tweet_media)

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
        text = (line.rstrip() for line in twt)
        text = list(line for line in text if line)
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

    @param twitter api
    @param list of text to tweet
    @param string username to tweet to
    @param list of media file paths
    '''    
    def __init__(self, twatter_api, text, victim, log, print_out, media=None):
        Thread.__init__(self)
        global b_prefix
        global g_prefix
        self.twatter_api = twatter_api
        self.media_list = media
        self.text_list = text
        self.victim = victim
        self.tweet_ids = []
        self.log = log
        self.print_out = print_out

    def run(self):
        '''
        Bot worker thread function

        @param none
        @return on Tweepy error
        @return on IndexError
        '''
        self.log.info(self.twatter_api.me().screen_name+" thread started")
        if self.media_list is None:
            self.media_list = []
        while True:
            try:
                for tweet in self.twatter_api.user_timeline(screen_name=self.victim, count=1):
                    # Find latest tweet that is less than five minutes old
                    if ((time.time() - (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds() < 300) and
                        (tweet.id not in self.tweet_ids)):
                        self.tweet_ids.append(tweet.id)
                        try:
                        reply = self.text_list.pop(0)
                        media = ""
                        if len(self.media_list) > 0: # Reply with media if there it exists
                            media = self.media_list.pop(0)
                            self.twatter_api.update_with_media(media,reply, in_reply_to_status_id=tweet.id)
                        else: # Otherwise reply with text only
                            self.twatter_api.update_status(reply, in_reply_to_status_id=tweet.id)

                        if media == "":
                            media = "<none>"
                        print("Reply: "+reply+" sent to @"+self.victim+" With file: "+media)
                        self.log.info("Reply: "+reply+" sent to @"+self.victim+" With file: "+media)
            except tweepy.TweepError as e: # Catch error and return
                if e.api_code == 88:
                    print(b_prefix+self.twatter_api.me().screen_name+" [Rate limited] "+str(e))
                elif e.api_code == 64:
                    print(b_prefix+self.twatter_api.me().screen_name+" [Suspended] "+str(e))
                elif e.api_code == 136:
                    print(b_prefix+self.twatter_api.me().screen_name+" [Blocked] "+str(e))
                elif e.api_code == 503:
                    time.sleep(5)
                    continue
                else:
                    print(b_prefix+self.twatter_api.me().screen_name+" [Other] "+str(e))
                self.log.info("Twitter Error: "+str(e))
                return
            except IndexError:
                print(b_prefix+self.twatter_api.me().screen_name+" is out of text to tweet")
                self.log.info("Wordlist empty. Killing "+self.twatter_api.me().screen_name+" bot")
                return

            time.sleep(2)

if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
    main()
