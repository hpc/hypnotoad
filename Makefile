all:
	@echo "This makefile is only for cleaning pyc files. You don't need to build anything."
	@echo "Run 'make clean' to remove all pyc files."

clean:
	-find ./ -name "*.pyc" -exec rm {} \; 
