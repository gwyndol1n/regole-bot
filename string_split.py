message_commands = {}

messages_config_file = open("message_commands.txt", "r+")
for line in messages_config_file:
	message_commands[line.split('|')[0]] = [line.split('|')[1], "{}".format(line.split('|')[2].rstrip())]

try:
	print(message_commands)
except:
	print("Can't do it")