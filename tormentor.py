#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy, time, sys, datetime, os, re
import argparse, traceback, time, datetime
import logging
from threading import Thread

'''
▄▄▄▄▄      ▄▄▄  • ▌ ▄ ·. ▄▄▄ . ▐ ▄ ▄▄▄▄▄      ▄▄▄  
•██  ▪     ▀▄ █··██ ▐███▪▀▄.▀·•█▌▐█•██  ▪     ▀▄ █·
 ▐█.▪ ▄█▀▄ ▐▀▀▄ ▐█ ▌▐▌▐█·▐▀▀▪▄▐█▐▐▌ ▐█.▪ ▄█▀▄ ▐▀▀▄ 
 ▐█▌·▐█▌.▐▌▐█•█▌██ ██▌▐█▌▐█▄▄▌██▐█▌ ▐█▌·▐█▌.▐▌▐█•█▌
 ▀▀▀  ▀█▄▀▪.▀  ▀▀▀  █▪▀▀▀ ▀▀▀ ▀▀ █▪ ▀▀▀  ▀█▄▀▪.▀  ▀
       Welcome to the Twitter Tormentor.
       
    Your friendly multi-threaded, multi-target
          Twitter harassment machine.
'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o','--printout',action='store_true',dest='out',help='Print all activity to stdout')
    reqd = parser.add_argument_group('required arguments')
    reqd.add_argument('-c','--config',action='store',dest='con',help='Path to config file',required=True)
    reqd.add_argument('-v', '--victim',action='store',dest='vic',help='Path to username file',required=True)
    args = parser.parse_args()
    
    if not os.path.isdir('logs/'):
        os.mkdir('logs/')
        log = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S', filename='logs/torment.log', filemode='w')
    else:
        log = logging.getLogger('logs/torment.log')
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S', filename=log.name, filemode='a')

    prefix = []
    try:
        import colorama
        from colorama import Fore, Style
        prefix.append("["+Fore.RED+" FAIL "+Style.RESET_ALL+"] ")
        prefix.append("["+Fore.GREEN+"  OK  "+Style.RESET_ALL+"] ")
        banner = Fore.RED+_get_banner()+Style.RESET_ALL
    except ImportError:
        prefix.append("[ FAIL ] ")
        prefix.append("[  OK  ] ")
        banner = _get_banner()
        
    print(banner)
    time.sleep(1)
    print(prefix[1]+"Fetching config")
    try:
        keys = _get_keys(args.con)
        victims = _get_victims(args.vic)
    except IOError as e:
        log.error(str(e)+": "+args.con)
        print(prefix[0]+str(e))
        sys.exit(1)
    except ValueError as e:
        log.error(str(e)+": "+args.vic)
        print(prefix[0]+str(e))
        sys.exit(1)
        
    print(prefix[1]+"Authenticating with Twitter")
    try:
        api_list = _get_twitter_api(keys)
    except tweepy.TweepError as e:
        log.error("Auth error: "+str(e))
        print(prefix[0]+"Twitter auth error in one or more users.  Check log")
        sys.exit(1)
        
    time.sleep(2)
    threads = []
    for api in api_list:
        list_vic = victims
        more = True
        
        while more:
            victim_list = []
            print(prefix[1]+"Select from list:")
            i = 0
            
            for vic in list_vic:
                print("\t["+str(i)+"] "+vic)
                i += 1
            res = input(prefix[1]+"Who should "+api.me().screen_name+" torment? ")
            
            if int(res) >= 0 and int(res) < len(list_vic):
                wl = input(prefix[1]+'Give me the path to '+list_vic[int(res)].strip()+' wordlist: ')
                try:
                    tmp_wl_txt = _get_tweet_text(wl)
                except IOError:
                    log.error("File not found: "+wl)
                    print(prefix[0]+wl+" not found.  Try again")
                    continue
                m = input(prefix[1]+'Give me the path to '+list_vic[int(res)].strip()+' media directory, or <ENTER> for none: ')
                try:
                    if m != "":
                        tmp_m_txt = _get_media_files(m)
                    else:
                        tmp_m_txt = None
                except IOError:
                    log.error("Files not found: "+m)
                    print(prefix[0]+m+" not found.  Try again")
                    continue
                    
                victim_list.append(Victim(list_vic[int(res)]))                
                victim_list[len(victim_list)-1].set_words(tmp_wl_txt)
                victim_list[len(victim_list)-1].set_media(tmp_m_txt)
                
                rep = input(prefix[1]+"Continue running this wordlist indefinitely [y/n]?: ")
                if rep.lower() == "y" or rep.lower() == "yes":
                    victim_list[len(victim_list)-1].set_repeat(True)
                
            list_vic.pop(int(res))

            soldier = Soldier(api, victim_list, log, prefix, args.out, keys)
            soldier.daemon = True
            threads.append(soldier)
            
            if len(list_vic) > 0:
                cont = input(prefix[1]+"Add another victim? [Y/N]: ")
                if cont.lower() == 'n' or cont.lower() == "no" or cont.lower() == "" or cont.lower() == " ":
                    more = False
            else:
                more = False
                
    print(prefix[1]+"Starting bot threads")
    try:
        for bot in threads:
            bot.start()
        log.info("Threads running")
        print(prefix[1]+"Bots running")
        for bot in threads:
            bot.join()
        log.info("All threads done")
        print(prefix[1]+"All bot threads are done")
    except KeyboardInterrupt:
        log.warning("User interrupt")
        
        print('\n'+prefix[1]+"User interrupt")
        print(prefix[1]+"Killing threads")
        
    except Exception as e:
        log.error("Error: "+str(e))
        print(prefix[0]+"Error: "+str(e))
        print(prefix[0]+str(traceback.print_exc()))  

    sys.exit(0)

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
  
def _get_victims(fp):
    '''
    Get list of users to torment

    @param string file path
    @return list users
    '''
    torment = []
    with open(fp,'r') as in_file:
        torment = [x.strip() for x in in_file.readlines()]
        if not isinstance(torment, list) and ',' in torment:
            raise ValueError("Comma separated list not supported")
    return torment
        
def _get_keys(fp):
    '''
    Get user api keys from config file

    @param string file path
    @return list (user, api_key_list)
    '''
    keys = []
    user_keys = []
    try:
        with open(fp,'r') as f:
            keys = [x.strip() for x in f.readlines()]
    except IOError:
        raise IOError("Config file not found")

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
    
class Victim:
    '''
    Store victim information
    
    @param string Twitter user name
    '''
    def __init__(self, name):
        self.name = name
        self.media = None
        self.repeat = False
        
    def set_words(self, words):
        self.wordlist = words
        self.refresh_words = words
        
    def set_media(self, media):
        self.media = media
        
    def set_repeat(self, repeat):
        self.repeat = repeat
        
class Soldier(Thread):
    '''
    Bot thread

    @param twitter api
    @param list of victim objects
    @param log
    @param prefix list
    ''' 
    def __init__(self, api, vic_list ,log, prefix, stdout, keys):
        Thread.__init__(self)
        self.api = api
        self.vic_list = vic_list
        self.log = log
        self.tweet_ids = []
        self.prefix = prefix
        self.stdout = stdout
        self.keys = keys
        
    def run(self):
        '''
        Bot worker thread function

        @param none
        @return on Tweepy error
        @return on IndexError
        '''
        self.log.info(self.api.me().screen_name+" thread started")
        reconnects = 0
        wifi = 0
        while True:
            for vic in self.vic_list:
                try:
                    for tweet in self.api.user_timeline(screen_name=vic.name, count=1):
                        # Find latest tweet that is less than five minutes old
                        if ((time.time() - (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds() < 300) and
                            (tweet.id not in self.tweet_ids)):
                            # Make sure it's not a retweet
                            if (not tweet.retweeted) and ('RT @' not in tweet.text):
                                self.tweet_ids.append(tweet.id)
                                reply = vic.wordlist.pop(0)
                                if vic.media is not None:
                                    media = vic.media.pop(0)
                                    self.api.update_with_media(media, vic.name+" "+reply, in_reply_to_status_id=tweet.id)
                                    if self.stdout:
                                        print(self.prefix[1]+"Reply: "+reply+" sent to: "+vic.name+" with file: "+str(media))
                                    self.log.info("Reply: "+reply+" sent to: "+vic.name+" with file: "+str(media))
                                else:
                                    self.api.update_status(vic.name+" "+reply, in_reply_to_status_id=tweet.id)
                                    if self.stdout:
                                        print(self.prefix[1]+"Reply: "+reply+" sent to: "+vic.name)
                                    self.log.info("Reply: "+reply+" sent to: "+vic.name)
                except tweepy.TweepError as e: # Catch error and return
                    if e.api_code == 88:
                        print(self.prefix[0]+self.api.me().screen_name+" [Rate limited] Taking a 15 second break "+str(e))
                        self.log.error(self.prefix[0]+self.api.me().screen_name+" [Rate limited] Taking a 15 second break "+str(e))
                        time.sleep(15)
                        continue
                    elif e.api_code == 64:
                        print(self.prefix[0]+self.api.me().screen_name+" [Suspended] "+str(e))
                        self.log.error(self.prefix[0]+self.api.me().screen_name+" [Suspended] "+str(e))
                    elif "HTTPSConnectionPool" in str(e):
                        if reconnects < 3:
                            print(self.prefix[0]+self.api.me().screen_name+" [HTTPS Error] Respawning API OBJ: "+str(e))
                            self.log.error(self.prefix[0]+self.api.me().screen_name+" [HTTPS Error] Respawning API OBJ: "+str(e))
                            time.sleep(5)
                            self.api = self._get_twitter_api(self.keys)
                            reconnects += 1
                            continue
                        else:
                            print(self.prefix[0]+self.api.me().screen_name+" [HTTPS Error] Exceeded reconnect limit. Aborting: "+str(e))
                            self.log.error(self.prefix[0]+self.api.me().screen_name+" [HTTPS Error] Exceeded reconnect limit. Aborting: "+str(e))
                    elif e.api_code == 136:
                        print(self.prefix[0]+self.api.me().screen_name+" [Blocked] "+str(e))
                        self.log.error(self.prefix[0]+self.api.me().screen_name+" [Blocked] "+str(e))
                    elif e.api_code == 186:
                        print(self.prefix[0]+self.api.me().screen_name+" [Tweet too Long] Skipping line and continuing: "+str(e))
                        self.log.error(self.prefix[0]+self.api.me().screen_name+" [Tweet too Long] Skipping line and continuing: "+str(e))
                        continue
                    elif e.api_code == 187:
                        print(self.prefix[0]+self.api.me().screen_name+" [Duplicate Tweet]. Fix wordlist. Aborting")
                        self.log.error(self.prefix[0]+self.api.me().screen_name+" [Duplicate Tweet] "+str(e))  
                    elif e.api_code == 503 or e.api_code == 130:
                        print(self.prefix[0]+"Over capacity - taking a break and trying again.: "+str(e))
                        self.log.info("Over capacity - taking a break and trying again.: "+str(e))
                        time.sleep(3)
                        continue
                    else:
                        print(self.prefix[0]+self.api.me().screen_name+" [Other] "+str(e))
                    return
                except IndexError:
                    print(self.prefix[0]+vic.name+" is out of text to tweet")
                    self.log.info(vic.name+" Wordlist empty.")
                    if vic.repeat == False:
                        self.vic_list.pop(self.vic_list.index(vic.name))
                        if len(vic_list) == 0:
                            return
                    else:
                        vic.wordlist = vic.refresh_words
                        print(self.prefix[0]+"Refreshing "+vic.name+" wordlist")
                        self.log.info("Refreshing "+vic.name+" wordlist and restarting")
                        continue
                except OSError as e:
                    if wifi < 3
                        print("Network error, taking a timeout to see if it comes back.")
                        self.log.info("Network error, taking a timeout to see if it comes back.")
                        time.sleep(60)
                        wifi += 1
                    else:
                        print("Network is dead. I'm out")
                        self.log.info("Network error.  It's not coming back.  Killing thread")
                        return
                except KeyboardInterrupt:
                    return

            time.sleep(2)

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
            
def _get_banner():
    return '''
    
▄▄▄▄▄      ▄▄▄  • ▌ ▄ ·. ▄▄▄ . ▐ ▄ ▄▄▄▄▄      ▄▄▄  
•██  ▪     ▀▄ █··██ ▐███▪▀▄.▀·•█▌▐█•██  ▪     ▀▄ █·
 ▐█.▪ ▄█▀▄ ▐▀▀▄ ▐█ ▌▐▌▐█·▐▀▀▪▄▐█▐▐▌ ▐█.▪ ▄█▀▄ ▐▀▀▄ 
 ▐█▌·▐█▌.▐▌▐█•█▌██ ██▌▐█▌▐█▄▄▌██▐█▌ ▐█▌·▐█▌.▐▌▐█•█▌
 ▀▀▀  ▀█▄▀▪.▀  ▀▀▀  █▪▀▀▀ ▀▀▀ ▀▀ █▪ ▀▀▀  ▀█▄▀▪.▀  ▀
       Welcome to the Twitter Tormentor.
       
    Your friendly multi-threaded, multi-target
          Twitter harassment machine.
    '''

if __name__ == "__main__":
    main()