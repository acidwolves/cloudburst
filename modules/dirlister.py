import os
import getpass

def run(**args):
	print '[*] In dirlister module'
	files = os.listdir('.')

	return str(files), str(getpass.getuser())+'_dirs'