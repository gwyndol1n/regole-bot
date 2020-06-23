# RegoleBot, v 1.3
# written by: Jimmy Kidd
# @jimothyjam
#
# some logic borrowed from Twitch API examples
# written for @RegoleSlayer, twitch.tv/regoleslayer
# 
#
#
#
#

import sys
import irc.bot
import requests
from enum import Enum
from secrets import *

class RegoleBot(irc.bot.SingleServerIRCBot):
	def __init__(self, username, client_id, token, channel):
		self.client_id = client_id
		self.token = token
		self.channel = '#' + channel

		# TODO: set up assoc array for counts, same as message commands
		self.death_count = 0
		self.run_count = 0

		self.account_permissions = {
			"broadcaster": 0, # highest level of permission; can call all commands, special commands
			"mod": 1, # next highest level; can do everything but make commands essentially
			"subscriber": 2, # might can do sub-specific commands, not sure on implementation yet
			"viewer": 3 # !run commands and such
		}

		# TODO: make dict of simple chat message commands
		self.message_commands = {}

		self.messages_config_file = open("message_commands.txt", "r+")
		for line in self.messages_config_file:
			self.message_commands[line.split('|')[0]] = [int(line.split('|')[1]), "{}".format(line.split('|')[2].rstrip())]

		# get channel ID
		url = 'https://api.twitch.tv/kraken/users?login=' + channel
		headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
		r = requests.get(url, headers = headers).json()
		self.channel_id = r['users'][0]['_id']

		# create connection
		server = 'irc.chat.twitch.tv'
		port = 6667
		print("Connecting to {} on port {}...".format(server, str(port)))
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port, token)], username, username) 

	def on_welcome(self, c, e):
		print('Joining ' + self.channel)

		#request capabilities
		c.cap('REQ', ':twitch.tv/membership')
		c.cap('REQ', ':twitch.tv/tags')
		c.cap('REQ', ':twitch.tv/commands')
		c.join(self.channel)

	def on_pubmsg(self, c, e):
		# try running !<message> as commands
		if e.arguments[0][:1] == '!':
			print(e.tags)
			# get command
			cmd = e.arguments[0].split(' ')[0][1:]
			# get display name
			self.display_name = e.tags[2]['value']

			# get argument, removes !<command>
			arg = e.arguments[0].replace("!{} ".format(cmd), '')
			
			# if arguments exist
			if arg != ("!{}".format(cmd)):
				print("Received command: {}, arg \"{}\" from {}".format(cmd, str(arg), self.display_name))
			else:
				print("Received command: {} from {}".format(cmd, self.display_name))

			self.do_command(e, cmd, arg)
		return

	def do_command(self, e, cmd, arg=None):
		c = self.connection
		url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
		headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
		r = requests.get(url, headers=headers).json()
		messages = self.message_commands
		permissions = self.account_permissions

		# set permissions from tags of event
		for tag in e.tags:
			if tag['key'] == 'mod' and int(tag['value']) == 1:
				permission_level = permissions['mod']
				break
			elif tag['key'] == 'display-name' and (tag['value'] == 'RegoleSlayer' or tag['value'] == 'JimothyJam'):
				permission_level = permissions['broadcaster']
				break
			elif tag['key'] == 'subscriber' and int(tag['value']) == 1:
				permission_level = permissions['subscriber']
				break
			#TODO: check for other flags here, like sub, streamer, etc.

		# if no other permission levels were set, set viewer permission level
		try:
			permission_level
		except NameError:
			permission_level = permissions['viewer']

		# if the command issued is a key in message_commands, send message string (0 is permission level)
		# if message permission level >= user permission level, print
		if cmd in messages and messages[cmd][0] >= permission_level:
			c.privmsg(self.channel, messages[cmd][1])

		# 	#TODO: Zane-only command to update text file

		# 	else:
		# 		None
		elif cmd == "adddeath" and permission_level <= 1:
			self.death_count = self.death_count + 1
			message = "Current death count: {}".format(self.death_count)
			c.privmsg(self.channel, message)

		# set current deaths, usage: !setdeath <number>
		elif cmd == "setdeath" and arg != None and permission_level <= 1:
			self.death_count = int(arg)
			message = "Death count set to {}.".format(self.death_count)
			c.privmsg(self.channel, message)

		elif cmd == "death" or cmd == "deaths":
			message = "Current death count: {}".format(self.death_count)	
			c.privmsg(self.channel, message)

		elif cmd == "addruncount" and permission_level <= 1:			
			self.run_count = self.run_count + 1
			message = "Current No Death run count: {}".format(self.run_count)
			c.privmsg(self.channel, message)

		# set current deaths, usage: !setruncount <number>
		elif cmd == "setruncount" and arg != None and permission_level <= 1:
			self.run_count = int(arg)
			message = "No Death run count set to {}.".format(self.run_count)
			c.privmsg(self.channel, message)

		elif cmd == "runcount":
			message = "Current No Death run count: {}".format(self.run_count)
			c.privmsg(self.channel, message)

		elif cmd == "updateoverlay" and permission_level == 0:
			if arg != None:
				overlay_txt = open("overlay_text.txt", "w")
				overlay_txt.write(arg)
				message = "Overlay updated."
				c.privmsg(self.channel, message)

			else: 	
				message = "Usage: !updateoverlay <text>"
				c.privmsg(self.channel, message)

		# create simple message command
		# elif cmd == "createcommand" and permission_level == 0:

		else:
			None

def main():
	if len(sys.argv) != 3:
		print("Usage: regolebot <username> <channel>")
		sys.exit(1)

	username  = sys.argv[1]
	client_id = client_id
	token     = token
	channel   = sys.argv[2]

	bot = RegoleBot(username, client_id, token, channel)
	bot.start()

if __name__ == "__main__":
	main()