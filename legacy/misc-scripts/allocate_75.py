#!/usr/bin/python

import sys
import array
import re
import string


if len(sys.argv) > 1:
	f = open(sys.argv[1])
	file = []
	record =0
	clusters=[]
	out = []
	skip=0
	verbose =0

	for line in f:
		file.append(line)
		grid = []
		grid = line.split(",")
		if len(grid) > 1:
			if grid[1] == 'Allocation Project Name' or grid[1] == '\"Allocation Project Name\"':
				record = 1
				x=2
				while (not re.search("..*Share", grid[x]) and x < len(grid)):
					grid[x] = grid[x].replace("\"", "")
					grid[x] = grid[x].replace("\s*", "")
					clusters.append(grid[x])
					out.append("")
					#print "test2"
					x += 1
			else:
				if re.search("Allocated to Projects", grid[1]):
					record = 0
					
				if record == 1:
					for y in range(len(clusters)):
						skip=0
						grid[1] = grid[1].replace("\"", "")
						if (not re.search("^\d+.\d+$", grid[y+2])):
							if (grid[y+2] == ''):
								skip =1
							else:
								grid[y+2] = "0"
						if (not re.search("^\d+.\d+$", grid[y+len(clusters) +2])):
							if (grid[y+len(clusters) +2] == ''):
								skip=1
							else:
								grid[y+len(clusters) +2] = "0"
						if (grid[1] != "" and skip != 1):
							out[y] += grid[1] + "\t" + grid[y+2] + "\t" + grid[y+len(clusters) +2] + "\n"
	f.close()
	for x in range(len(clusters)):
		output = ""
		total = 0
		totalcpuhrs = 0
		output += "## %10s %10s %10s\n" % ('Project', 'Cpu Hours', 'Percentage')
		output += "#----------# \n" * 3;
		for line in out[x].split("\n"):
			if (line != ""):
				if (verbose == 1):
					print line
				vals = line.split()
				project = vals[0]
				cpuhrs = float(vals[1])
				percentage = float(vals[2])
				percentage = (percentage) *100
		 		output += "# Project:%s        Hours:%2.3f\n" % (project, cpuhrs)
		 		output += "QOSCFG[%s]          FSTARGET=%2.6f\n" % (project, percentage)
		 		output += "ACCOUNTCFG[%s]   QDEF=%s  FSTARGET=4\n" % (project, project)
		 		output += "#\n"
	 			total += percentage
				totalcpuhrs += cpuhrs
		
		output += "\n#Total percentage : %2.2f\n" % total
		output += "\n#Total allocation hours: %2.3f\n" % totalcpuhrs

		f = open(clusters[x] + ".txt", 'w')
		f.write(output)
		f.close();
		


else:
	print "Error: please enter a file name\n"
	print "Usage allocate.py <file>.csv\n"
