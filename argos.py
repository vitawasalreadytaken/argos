#!/usr/bin/env python

from __future__ import unicode_literals
import collections, json, os, random, requests, sh, shelve, sys, time
from multiprocessing.pool import ThreadPool



HttpCheckResult = collections.namedtuple('HttpCheckResult', ('target', 'status', 'content'))



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
		return HttpCheckResult(target, r.status_code, headers + '\n\n' + r.text)
	except requests.exceptions.Timeout:
		return HttpCheckResult(target, 'timeout (>{0}s)'.format(timeout), None)



def parallelHttpCheck(targets, timeout):
	pool = ThreadPool(processes = min(len(targets), 10))
	asyncs = [ pool.apply_async(httpCheck, args = (target, timeout)) for target in targets ]
	return [ a.get() for a in asyncs ]



def generateReport(results):
	summary = ', '.join([ '{0}: {1}'.format(r.target['url'], r.status) for r in results ])
	detail = '\n\n\n\n'.join([ '*** {0}: {1}\n\n{2}'.format(r.target['url'], r.status, r.content) for r in results ])
	return (summary, detail)



def emailReport(mandrillEndpoint, mandrillKey, fromEmail, fromName, toEmails, summary, detail):
	payload = {
		'key': mandrillKey,
		'message': {
			'subject': summary,
			'text': detail,
			'from_email': fromEmail,
			'from_name': fromName,
			'to': [ {'email': to} for to in toEmails ]
		}
	}
	r = requests.post(mandrillEndpoint, data = json.dumps(payload))
	return r.json()



def canSendReport(target, reportTimes, minInterval):
	key = str(target['url'])
	return (key not in reportTimes) or (time.time() - reportTimes[key] >= minInterval)



def filterAlerts(results, alertIndicator, reportTimes, minReportInterval):
	alerts = []
	for result in results:
		key = str(result.target['url'])
		if alertIndicator(result): # This is an alert.
			if canSendReport(result.target, reportTimes, minReportInterval):
				alerts.append(result)
				reportTimes[key] = time.time()
		else:
			if key in reportTimes:
				del reportTimes[key]

	return (alerts, reportTimes)



def setupCron(period):
	randomShift = random.randint(0, period - 1)
	minutes = range(randomShift, 60, period)
	# m h dom mon dow command
	line = '{0} * * * * {1}'.format(','.join(map(str, minutes)), os.path.abspath(__file__))
	print 'Adding the following line to crontab:'
	print '  ', line
	current = unicode(sh.crontab('-l'))
	this = os.path.basename(__file__)
	if current.find(this) > -1:
		print '\nERROR: your current crontab already contains a reference to {0}:\n'.format(this)
		print current
		return 2

	new = current + '\n\n' + line + '\n'
	sh.crontab('-', _in = new)
	print 'Your new crontab is:\n'
	print sh.crontab('-l')







def main(argv, settings):
	allowedCommands = ('http-check', 'setup-cron',)

	# Validate and parse commands.
	if len(argv) != 2 or argv[1] not in allowedCommands:
		print 'Usage: {0} {1}'.format(argv[0], '|'.join(allowedCommands))
		return 1
	command = argv[1]

	# Open (and possibly initialize) our state database.
	state = shelve.open(settings.STATE_DB, writeback = True)
	if not str('reportTimes') in state:
		state['reportTimes'] = {}

	# Execute.
	if command == 'http-check':
		targets = getTargets(settings.TARGET_CONF_URLS, settings.TARGET_CONF_TIMEOUT)
		results = parallelHttpCheck(targets, settings.HTTP_CHECK_TIMEOUT)

		(alerts, state['reportTimes']) = filterAlerts(results, settings.HTTP_ALERT_FILTER, state['reportTimes'], settings.MIN_REPORT_INTERVAL)

		if alerts:
			(summary, detail) = generateReport(alerts)
			r = emailReport(
				settings.MANDRILL_ENDPOINT, settings.MANDRILL_API_KEY,
				settings.EMAIL_FROM, settings.EMAIL_FROM_NAME, settings.EMAIL_TO,
				summary, detail
			)

	elif command == 'setup-cron':
		return setupCron(settings.CRON_PERIOD)

	state.close()





if __name__ == '__main__':
	import settings
	sys.exit(main(sys.argv, settings) or 0)
