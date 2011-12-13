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
	norm = [1, .25, .25, .75]
	skip=0
	verbose =0
	tmptest = 0.0
	totals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
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
					x += 1
			else:
				if (re.search("Allocated to Projects", grid[1])):
					record =0;
				if (record == 1):
					for y in range(len(clusters)):
						skip=0
						grid[1] = grid[1].replace("\"", "")
						if (not (re.search("^\s*\d+.\d+\s*$", grid[y+2]) or (re.search("^\s*\d+\s*$", grid[y+2])))):
							if (not re.search("^\d+$", grid[0])):
								skip=1
							else:
								grid[y+2] = "0"
						if ((re.search("^\d+$", grid[y+2]) or re.search("\d+.\d+", grid[y+2])) and skip == 0):
							totals[y]+=float(grid[y+2])
				
				
					
		
	f.close()
	f = open(sys.argv[1])
	record =0
	for x in range(len(clusters)):
		norm[x]=input("Enter a normalization for " + clusters[x] + ": ");
	for line in f:
		file.append(line)
		grid = []
		grid = line.split(",")
		if len(grid) > 1:
			if grid[1] == 'Allocation Project Name' or grid[1] == '\"Allocation Project Name\"':
				record = 1
			else:
				if re.search("Allocated to Projects", grid[1]):
					record = 0
					
				if record == 1:
					for y in range(len(clusters)):
						skip=0
						grid[1] = grid[1].replace("\"", "")
						if (not (re.search("^\s*\d+.\d+\s*$", grid[y+2]) or (re.search("^\s*\d+\s*$", grid[y+2])))):
							if (not re.search("^\d+$", grid[0])):
								skip=1
							else:
								grid[y+2] = "0"
						if (skip == 0):
							if (float(grid[y+2]) == 0):
								skip=1
							
						if (grid[1] != "" and skip != 1 ):
							tmpTotal = (float(grid[y+2])/totals[y]) * norm[y]
							print "tmptotal:";
							print tmpTotal;
							print "/";
							print totals[y];
							print "\n";
							out[y] += grid[1] + "\t" + grid[y+2] + "\t" + str(tmpTotal) + "\n"
	f.close()
	for x in range(len(clusters)):
		output = ""
		total = 0
		totalcpuhrs = 0
		output += "## %10s %10s %10s\n" % ('Project', 'Cpu Hours', 'Percentage')
		output += "#----------# \n" * 3;
		output += "# Normalized to " + str(norm[x]* 100) + "%.\n\n"
		output += "#Total allocation hours: " + str(totals[x]) + ".\n\n"
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
		 		output += "QOSCFG[%s]          FSTARGET=%2.6f\n" % (project,percentage)
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
