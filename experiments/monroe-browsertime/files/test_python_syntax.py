import sys
filename = sys.argv[1]
source = open(filename, 'r').read() + '\n'
compile(source, filename, 'exec')
