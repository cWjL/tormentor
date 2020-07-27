# tormentor

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
With `<key>` and `<secret>` being the API keys obtained from Twitter, in string format.  The `KEY`, `<value>` pairs must be tab separated.<br />

Each `@<user>` will create an individual bot, each with their own list of targets (users to torment) and associated word and media lists [all of which will be set up at runtime].<br />

The bot targets (users to respond to) must be passed at runtime using the `-v` or `--victim` flags and must be a list of Twitter screenames.<br />
```
	@Victim1
	@Victim2
	@Victim3
```
Use `-o` or `--printout` to print all bot responses to stdout.<br />

**Python Version**
```
Python3.X
```

**Required Packages**

&nbsp;&nbsp;install requirements
```
pip install -r requirements.txt
```
&nbsp;&nbsp;or
```
python3 -m pip install -r requirements.txt
```

**Usage**
```
usage: tormentor.py [-h] [-o] -c CON -v VIC

optional arguments:
  -h, --help            show this help message and exit
  -o, --printout        Print all activity to stdout

required arguments:
  -c CON, --config CON  Path to config file
  -v VIC, --victim VIC  Path to username file
```

**Usage Example**
```
./tormentor.py -c config.conf -v victims.txt -o
```
