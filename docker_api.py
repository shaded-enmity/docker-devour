#!/bin/python -tt
#vim: set fileencoding=utf-8 :
# Part of Docker Devour project

from devourutil import flag_gen

'''
 Class describing a generic
 Docker Remote API request
'''
class DockerAPIRequest(object):
	def __init__(self):
		self.desc = ''
		self.type = ''
		self.url = ''
		self.url_sub = []
		self.get_params = []
		self.filters = []
		self.json = []
		self.status = []
		self.headers = []

	@staticmethod
	def new(**kv):
		dar = DockerAPIRequest()
		for (key, value) in kv.iteritems():
			setattr(dar, key, value)
		return dar

'''
 We can have 1 Verb, N flags, and N context args
'''
class ArgType(object):
	(Invalid, Verb, Flag, Context) = range(4)

'''
 Enumeration of Docker CLI sub-commands or "verbs".
'''
class DockerVerb(object):
	(Invalid, Attach, Build, Commit, Cp, Create, 
	 Diff, Events, Exec, Export, History, Images, 
	 Import, Info, Inspect, Kill, Load, Login, 
	 Logout, Logs, Port, Pause, Ps, Pull, Push, 
	 Restart, Rm, Rmi, Run, Save, Search, Start, 
	 Stop, Tag, Top, Unpause) = range(36)

'''
 Class describing what kind of information
 is stored in the flag.

 `PureBool` specifies a flag which is toggled
 if no explicit value is specified (i.e. you 
 don't need to write --verbose=true)
'''
class FlagType(object):
	(Invalid, Bool, Int, String, Path, Pure, FauxVerb) = flag_gen(7)
	PureBool = Bool | Pure

'''
 - / -- flags for the Docker CLI
'''
class Flag(object):
	def __init__(self, names=[], type=FlagType.Invalid, value=None, default=None):
		self.names = names
		self.value = value
		self.type = type
		self.default = default

	def __repr__(self):
		s = ''
		for n in self.names:
			p = '-' if len(n) == 1 else '--'
			s = s + ' / ' + p + n
		return s[3:]
	
	@staticmethod
	def new(**kv):
		f = Flag()
		for (key, value) in kv.iteritems():
			setattr(f, key, value)
		return f


