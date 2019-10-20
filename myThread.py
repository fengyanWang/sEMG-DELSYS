#coding:UTF-8

import time
import ctypes
import inspect
import threading

class myThread(object):

	def __init__(self):

		self.threadList = []
		self.threadNameList = []

	def addThread(self, threadName , targetFunc , haveArgsFlag , args = (1,2)):
		if haveArgsFlag == 0:
			threadName = threading.Thread(target = targetFunc )
		else:
			threadName = threading.Thread(target = targetFunc , args = args)
		self.threadList.append(threadName)
		self.threadNameList.append(threadName)

	def delThread(self , threadName):
		if threadName in self.threadNameList:
			self.threadNameList.remove(threadName)
			self.threadList.remove(threadName)
		else:
			print(threadName + ' not be creat!!!!!!')
			
	def runThread(self):

		for t in self.threadList:
			t.start()

	def stopThread(self):
		for t in self.threadList:
			t.join()

	def forcedStopThread(self):
		for t in self.threadList:
			self.stop_thread(t)


	def _async_raise(self , tid, exctype):
	    """raises the exception, performs cleanup if needed"""
	    tid = ctypes.c_long(tid)
	    if not inspect.isclass(exctype):
	        exctype = type(exctype)
	    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
	    if res == 0:
	        raise ValueError("invalid thread id")
	    elif res != 1:
	        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
	        raise SystemError("PyThreadState_SetAsyncExc failed")

	def stop_thread(self , thread):
	    self._async_raise(thread.ident, SystemExit)