import os
import sys

currentPath = os.getcwd()
if not currentPath + '\\delsys' in sys.path:
	sys.path.append(currentPath + '\\delsys')

from delsysDataAcqure import myDelsys