#!/usr/bin/env python

from __future__ import unicode_literals
import requests, sys
from multiprocessing.pool import ThreadPool



def getTargets(confUrls, timeout):
	for url in confUrls:
		try:
			r = requests.get(url, timeout = timeout)
			if r.status_code == 200:
				return r.json()['targets']
		except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
			pass
	raise Exception('No target conf URLs could be reached. Tried {0}.'.format(confUrls))



def httpCheck(target, timeout):
	try:
		r = requests.get(target['url'], timeout = timeout)
		headers = '\n'.join([ '{0}: {1}'.format(k, v) for (k, v) in r.headers.items() ])
		return (target, r.status_code, headers + '\n\n' + r.text)
	except requests.exceptions.Timeout:
		return (target, 'timeout', None)



def parallelHttpCheck(targets, timeout):
	pool = ThreadPool(processes = min(len(targets), 10))
	asyncs = [ pool.apply_async(httpCheck, args = (target, timeout)) for target in targets ]
	return [ a.get() for a in asyncs ]



def generateReport(results, resultFilter = lambda (target, status, content): status != 200):
	results = filter(resultFilter, results)
	if not results:
		return (None, None)
	summary = ', '.join([ '{0}: {1}'.format(target['url'], status) for (target, status, content) in results ])
	detail = '\n\n\n\n'.join([ '*** {0}: {1}\n\n{2}'.format(target['url'], status, content) for (target, status, content) in results ])
	return (summary, detail)



def main(argv, settings):
	# The only command supported so far is 'http-check'.
	allowedCommands = ('http-check',)

	# Validate and parse commands.
	if len(argv) != 2 or argv[1] not in allowedCommands:
		print 'Usage: {0} {1}'.format(argv[0], '|'.join(allowedCommands))
		return 1
	command = argv[1]

	# Execute.
	if command == 'http-check':
		targets = getTargets(settings.TARGET_CONF_URLS, settings.TARGET_CONF_TIMEOUT)
		results = parallelHttpCheck(targets, settings.HTTP_CHECK_TIMEOUT)
		(summary, detail) = generateReport(results)
		print summary






if __name__ == '__main__':
	import settings
	sys.exit(main(sys.argv, settings) or 0)
