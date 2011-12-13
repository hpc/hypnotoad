#!/usr/bin/python
import commands,string,csv

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

print ' '

for commandName,commandResult in resultDict.iteritems():
#    print "Executed: %s"%commandName
     print "Result for:  %s"%commandResult
     print "-------------------------------------"
     print ' '
