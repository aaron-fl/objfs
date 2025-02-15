import os, traceback
from cli import exit, print, Table, CLR, ENV_PREFIX, Pretty


class Config():
	_targets = {}
	_implicit_targets = {'final', 'initial', 'container'}
	_instance = None


	def __new__(cls, *args, **kwargs):
		if kwargs: return super().__new__(cls)
		if Config._instance == None:
			Config._instance = super().__new__(cls)
		return Config._instance


	@classmethod
	def target_remove(self, *names):
		for name in names:
			del Config._targets[name]


	@classmethod
	def target(self, before=[], after=[], mutex=[]):
		def _target(fn):
			mutex.append(fn.__name__)
			Config._targets[fn.__name__] = {'before':before, 'after':after, 'mutex':mutex, 'fn':fn}
			return fn
		return _target


	@classmethod
	def all_targets(self):
		all = set()
		targets = [(t, self._targets[t]['before'], self._targets[t]['after'], self._targets[t]['mutex'])
			for t in list(self._targets.keys() - self._implicit_targets)]
		lbefore = -1
		while lbefore != len(all):
			lbefore = len(all)
			for tname, before, after, mutex in targets:
				if not (before or after):
					all.add(tname)
					continue
				def _excluded(t):
					for x in mutex:
						if x+'.' in t: return True
					return False
				for grp, end in [(before, 0), (after, -1)]:
					for t in list(all):
						if _excluded(t): continue
						if grp == True or t.split('.')[end] in grp:
							all.add(f'{t}.{tname}' if end else f'{tname}.{t}')
		return sorted(all)


	def __init__(self, **kwargs):
		# If we are using the cached _instance then don't initialize again
		if 'target' in self: return
		# load environment variables
		for k in os.environ:
			if k.startswith(ENV_PREFIX): kwargs.setdefault(k[len(ENV_PREFIX):].lower(), os.environ[k])
		# if it didn't get loaded from the environment
		kwargs.setdefault('target', 'local')
		for k in kwargs: setattr(self, k, kwargs[k])
		# Run the config handlers
		Config._targets['initial']['fn'](self)
		for target in self.target.split('.'):
			Config._targets[target]['fn'](self)
		Config._targets['final']['fn'](self)


	def __getitem__(self, name):
		return getattr(self, name)


	def __getattr__(self, name):
		tb = traceback.extract_stack(limit=3)
		tb = tb[0] if tb[1].filename.endswith('__init__.py') else tb[1]
		exit(print.ERR, f"'{name}' not found in target '{self.target}'", ['']*3, f"{os.path.relpath(tb.filename)}:{tb.lineno}:  {tb.line}")


	def __setitem__(self, name, val):
		return setattr(self, name, val)


	def __contains__(self, name):
		return name in self.__dict__


	def get(self, name, default=None):
		return self.__dict__[name] if name in self.__dict__ else default


	def setdefault(self, key, val):
		if key not in self.__dict__: setattr(self, key, val)


	def __pretty__(self):
		return Pretty({name:value for name, value in self})
		

	def __iter__(self):
		for d in self.__dict__:
			if not d.startswith('_') and d not in []: yield d, self[d]
