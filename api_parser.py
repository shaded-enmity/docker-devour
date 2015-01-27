#!/bin/python -tt
#vim: set fileencoding=utf-8 :

import sys, re, argparse, hashlib, os

from devourutil import flag_gen
from BeautifulSoup import BeautifulSoup

'''
 Docker Devour

 Parse the Docker remote API HTML descriptions
 into full blown code descriptions.
 Parse tree can be further used to generate
 compatible REST API for both the client/server.
 The output language is fully dependent on the
 format of the template passed in the -t / --template
 argument.
'''

parser = argparse.ArgumentParser()
parser.add_argument('api_file', help='Path to a HTML page specifying the API\
		or read from STDIN if -')
parser.add_argument('--verbose', '-v', help='Increase command verbosity',\
		action='store_true')
parser.add_argument('--values', '-V', help='Also dump the values of\
		parameters', action='store_true')
parser.add_argument('--template', '-t', help='Output template for the\
		request models')
parser.add_argument('--decoration', '-d', help='How to decorate strings\
		i.e. default is \'%%s\'', default='\'%s\'')
args = parser.parse_args()
verbose, api_file, values, template, deco = (args.verbose, args.api_file,\
		args.values, args.template, args.decoration)
rest_arg = re.compile('\(.+?\)')
header = re.compile('[A-Z]{1}[A-Za-z-]+')
skip_headers = ['Image tarball format']
has_json_header = ['POST /containers/(id)/exec', \
	'POST /exec/(id)/start', 'POST /commit', \
	'POST /containers/create']
query_header = re.compile('^Query Parameters?')
json_header = 'Json Parameters:'
status_header = 'Status Codes:'
NoExtents = (-1, -1)

class ParamType(object):
	'''
	 Holds the type of the parameter
	'''
	(Invalid, Query, Json, Status, QueryFilter, Header) = range(6)

class Param(object):
	'''
	 Generic mapping for different kinds of parameters
	'''
	Splitters = [u'–', u'-', u':'] # Let's just try to be consisten... uhm, what?

	def __init__(self, n='', d='', pt=ParamType.Invalid):
		self.name = n
		self.description = d
		self.type = pt

	def __repr__(self):
		txt = self.name
		if values:
			txt += '  %s' % self.description
		return txt

	@staticmethod
	def from_string(s, pt):
		'''
		 Parse a Param object from the string
		'''
		if s == u'HostConfig':
			return Param('HostConfig', '', pt)

		if pt == ParamType.QueryFilter:
			asunder = s.split('=', 1)
			return Param(asunder[0].strip(), asunder[1].strip(), pt)

		for split in Param.Splitters:
			asunder = s.split(split, 1)
			if len(asunder) == 2:
				return Param(asunder[0].strip(), asunder[1].strip(), pt)
		return None


class RequestMethod(object):
	'''
	 Convenient mapping from/to HTTP request methods
	'''
	(Invalid, Get, Post, Delete, Put) = flag_gen(5)

	@staticmethod
	def from_string(s=''):
		return {'GET': RequestMethod.Get, 
			'POST': RequestMethod.Post, 
			'DELETE': RequestMethod.Delete,
			'PUT': RequestMethod.Put}.get(s)

	@staticmethod
	def to_string(rm):
		return {RequestMethod.Invalid: 'INVALID',
			RequestMethod.Get: 'GET',
			RequestMethod.Post: 'POST',
			RequestMethod.Delete: 'DELETE',
			RequestMethod.Put: 'PUT'}.get(rm)


class RequestModel(object):
	'''
	 Stores all the info about a single request
	'''
	def __init__(self):
		self.method = RequestMethod.Invalid 
		self.query = ''
		self.rest_var_extents = []
		self.params = []
		self.status_codes = []
		self.description = ''

	def set_description(self, d):
		'''
		 Text description of the request
		'''
		self.description = d

	def set_method(self, m):
		'''
		 Set the HTTP request method
		'''
		self.method = RequestMethod.from_string(m)

	def set_query(self, q):
		'''
		 Set the query parameter and try to derive 
		 REST variable extents
		'''
		self.query = q
		var = rest_arg.finditer(q)
		for ex in var:
			self.rest_var_extents.append(ex.span(0))

	def add_filter_param(self, p, pt=ParamType.QueryFilter):
		'''
		 Possible filters
		'''
		if isinstance(p, unicode):
			p = Param.from_string(p, pt)
		self.params.append(p)

	def add_param(self, p, pt=ParamType.Invalid):
		'''
		 Query/JSON parameters
		'''
		if isinstance(p, unicode):
			p = Param.from_string(p, pt)
		self.params.append(p)

	def add_status_code(self, sc):
		'''
		 Possible HTTP status codes
		'''
		if isinstance(sc, unicode):
			sc = Param.from_string(sc)
		self.status_codes.append(sc)

	def params_by_type(self, pt):
		'''
		 Filter all the parameters by
		 the given `ParamType`.
		'''
		return (x for x in self.params if x.type == pt)

	def __repr__(self):
		buf = '- RequestModel:\n'
		buf+= '  Query:\n'
		buf+= '   %s %s \n' % (RequestMethod.to_string(self.method), self.query)

		if self.rest_var_extents:
			'''
			 If we have an embedded REST variables ...
			'''
			buf += "\n  REST Param:\n" 
			for rve in self.rest_var_extents:
				buf+='   %s at %s\n' % \
					(self.query[rve[0]+1:rve[1]-1],\
					str(rve))

		def format_param_group(group, header):
			params = [str(p) for p in self.params_by_type(group)]
			if not params:
				return ''
			return '\n  %s:\n   %s\n' % (header, '\n   '.join(params))

		buf += format_param_group(ParamType.Query, 'Params')
		buf += format_param_group(ParamType.QueryFilter, 'Filters')
		buf += format_param_group(ParamType.Json, 'JSON')
		buf += format_param_group(ParamType.Status, 'Status codes')
		buf += format_param_group(ParamType.Header, 'Headers')

		return buf

def sanitize(s=''):
	'''
	 Remove newlines
	'''
	return s.replace('\n' , '').replace('\r', '')

def params_to_json(lst):
	'''
	 Quote each string and place comma after
	'''
	return ', '.join([deco % x.name for x in lst])

def out_string(s):
	return deco % s.replace('\'', '\\\'')

def is_probably_header(s):
	'''
	 Heuristics to differentiate between GET params
	 and HTTP headers
	'''
	return header.match(s) != None


fd = open(api_file) if api_file != '-' else sys.stdin
if verbose:
	print 'Opening: "%s"' % api_file

tree = BeautifulSoup(fd)
content = tree.find('div', {'class': 'span9 content-body'})
request_models = []

if not content:
	print 'The content <DIV> was not found.'
	sys.exit(1)

content_hash = hashlib.sha256(str(content)).hexdigest()

for section_header in content.findAll('h3'):
	if section_header.string in skip_headers:
		continue

	in_query_filter = False
	request = RequestModel()
	request_string = section_header.findNext('code').string
	request.set_description(section_header.string)

	(method, query) = request_string.split(' ', 1)

	if verbose:
		print '  ─── (REQUEST) ', query

	request.set_method(method)
	request.set_query(query)

	if request_string in has_json_header:
		query = section_header.findNext('p', text=json_header)
		if query and query.findPrevious('h3') == section_header:
			for li in query.findNext('ul').findAll('li'):
				request.add_param(sanitize(li.text), ParamType.Json)
				if verbose:
					print '    ─── (JSON) ', sanitize(li.text)

	query = section_header.findNext('p', text=query_header)
	if query and query.findPrevious('h3') == section_header: 
		for li in query.findNext('ul').findAll('li'):
			if in_query_filter:
				if verbose:
					print '    ─── (FILTER) ', sanitize(li.text)
				request.add_filter_param(sanitize(li.text))
			else:
				if verbose:
					print '    ─── (QUERY) ', sanitize(li.text)
				if li.text.startswith('filters'):
					in_query_filter = True
				pt = ParamType.Query if not is_probably_header(li.text) else ParamType.Header
				request.add_param(sanitize(li.text), pt)

	query = section_header.findNext('p', text=status_header)
	if query and query.findPrevious('h3') == section_header:
		for li in query.findNext('ul').findAll('li'):
			failsafe = li.find('p')
			if failsafe:
				request.add_param(sanitize(failsafe.text), ParamType.Status)
				if verbose:
					print '    ─── (FS_STATUS) ', sanitize(failsafe.text)
				break
			else:
				request.add_param(sanitize(li.text), ParamType.Status)
				if verbose:
					print '    ─── (STATUS) ', sanitize(li.text)
	request_models.append(request)

tpl = None
if template:
	tpl = open(template).read()
	if os.path.isfile(template+'_header'):
		print open(template+'_header').read() % (sys.argv[0], content_hash)

for rm in request_models:
	if tpl:
		out_tpl = tpl
		out_tpl = out_tpl.replace('$REQUEST_DESCRIPTION', out_string(rm.description))
		out_tpl = out_tpl.replace('$REQUEST_TYPE', out_string(RequestMethod.to_string(rm.method)))
		out_tpl = out_tpl.replace('$REQUEST_URL', out_string(rm.query))

		out_tpl = out_tpl.replace('$REQUEST_SUB', str(list(rm.rest_var_extents)))

		out_tpl = out_tpl.replace('$REQUEST_GET_PARAMETERS', \
				params_to_json(rm.params_by_type(ParamType.Query)))
		out_tpl = out_tpl.replace('$REQUEST_FILTERS', \
				params_to_json(rm.params_by_type(ParamType.QueryFilter)))
		out_tpl = out_tpl.replace('$REQUEST_JSON_PARAMETERS', \
				params_to_json(rm.params_by_type(ParamType.Json)))
		out_tpl = out_tpl.replace('$REQUEST_STATUS_CODES', \
				params_to_json(rm.params_by_type(ParamType.Status)))
		out_tpl = out_tpl.replace('$REQUEST_HEADER_PARAMETERS', \
				params_to_json(rm.params_by_type(ParamType.Header)))

		print out_tpl
	else:
		print rm
		if api_file != '-' and raw_input('Continue? [Y/n]') in ['n', 'N']:
			break
