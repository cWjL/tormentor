# simple_bot

Simple multithreaded python Twitter bot.  Uses configuration file passed at runtime to define the number of threads to create.  Configuration file must be passed using either `-c` or `--config` flags and be in the following format:
```
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
```
With `<key>` and `<secret>` being the API keys obtained from Twitter, in string format.  The `CONSUMER_KEY` and `<key>` must be tab separated.<br />
The bot target (user to respond to) must be passed at runtime using the `-v` or `--victim` flags.<br />

**Required Packages**

&nbsp;&nbsp;tweepy
```
pip install tweepy
```

**Optional Packages**

&nbsp;&nbsp;tweepy
```
pip install tweepy
```

**Usage**
```
usage: simple_bot.py [-h] -c CON -v VIC

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -c CON, --config CON  Path to config file
  -v VIC, --victim VIC  Path to username file
```

**Usage Example**
```
./simple_bot.py -c config.conf -v victims.txt
```
