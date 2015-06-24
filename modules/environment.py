import os
import getpass

def run(**args):
	print '[*] In environment module'
	return str(os.environ), str(getpass.getuser())+'_environment'