#!/usr/bin/python
import commands,string,csv
import re

from optparse import OptionParser

def main():
	usage = "usage: %prog [options] arg"
	parser = OptionParser() 
        parser.add_option("-p", "--procs", dest="procs", help="Number of Procs needed for job.")
        (options, args) = parser.parse_args()
        if options.procs:
          print "reading %s..." % options.procs
          requestedprocs = options.procs
          print ' Requested procs %s' % requestedprocs


def writeMessage(self,message,result=''):
    dateTime=datetime.datetime.now()
    fileToWrite=open('/tmp/zenossErrorLog.txt','a')
    fileToWrite.write("\n------------------------------------\n")
    fileToWrite.write("Message Occurred at %s\n" %(dateTime))
    fileToWrite.write("Message: %s\n" %(str(message)))
    if result:
        fileToWrite.write("Result: %s\n" %(result))
    fileToWrite.write("------------------------------------\n")
    fileToWrite.close()

if __name__ == "__main__":
    main()
 
# get users moniker
name=commands.getoutput('logname')

print ' '
print ' '
print 'Hello ', 
print name,


# look for accounts in drm_drps.txt for a certain user
linefromdrmgrps=commands.getoutput('grep %s drm_grps.txt' %name)

withoutMoniker=linefromdrmgrps.lstrip(name)
print ' these are accounts you can use:',
print withoutMoniker

words = withoutMoniker.split(",")

print ' '
print 'Processors available and utilization:'
resultDict={}
for account in words:
    commandList=['showq | grep active','mdiag -c | grep %s' %account]

    for exeCommand in commandList:

	commandOutput=commands.getoutput(exeCommand)
     	resultDict[exeCommand]=commandOutput
	accountMatches = (re.findall('\\brequestedprocs\\b', commandOutput))
     	print 'Account= %s' %accountMatches

	print ' '

	for commandName,commandResult in resultDict.iteritems():
	        print "Executed: %s"%commandName
	     	print "Result for:  %s"%commandResult
     		print "-------------------------------------"
     		print ' '
