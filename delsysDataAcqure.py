"""
Tests communication with and data acquisition from a Delsys Trigno wireless
EMG system. Delsys Trigno Control Utility needs to be installed and running,
and the device needs to be plugged in. Tests can be run with a device connected
to a remote machine if needed.

The tests run by this script are very simple and are by no means exhaustive. It
just sets different numbers of channels and ensures the data received is the
correct shape.

Use `-h` or `--help` for options.
"""

import argparse
import time
import os
import csv
import numpy
import pandas as pd

try:
	import pytrigno
except ImportError:
	import sys
	sys.path.insert(0, '..')
	import pytrigno

class myDelsys(object):
	
	def __init__(self, dataFilePath , devType = ['emg' , 'acc'] , channel_range = [0,1] , emg_samples_per_read = 270 ,acc_samples_per_read = 9 , host = "localhost"):

		self.devType = devType
		self.channel_range = channel_range
		self.emg_samples_per_read = emg_samples_per_read
		self.acc_samples_per_read = acc_samples_per_read
		self.host = host
		self.dataFilePath = dataFilePath
		self.channel_number = len(self.channel_range)

		self.emgData = []
		self.imuData = []
		self.emgSaveCount = 5
		self.imuSaveCount = 5

		self.channelStrList = []

		self.emgDatacount = 0
		self.imuDatacount = 0
		
	def start(self):
		self.getChannelName()
		self.setTheIndex()
		if 'emg' in self.devType:
			self.emgDev =  pytrigno.TrignoEMG(self.channel_range ,self.emg_samples_per_read ,self.host)
			self.emgDev.start()
		if 'acc' in self.devType:
			self.accDev =  pytrigno.TrignoAccel(self.channel_range ,self.acc_samples_per_read ,self.host)
			self.accDev.start()
		
	def readEmgData(self):
		actionList = numpy.ones((1,270)) * (1) 
		data = self.emgDev.read()
		data = numpy.row_stack((data , actionList))
		self.emgData.extend(data.T) #the element of self.emgData is 'numpy.float64'
		self.emgDatacount += 1
		
	def readImuData(self):
		data = self.accDev.read()
		self.imuData.extend(data.T)

		self.imuDatacount += 1

	def createEmgDataFile(self ):
		if self.emgDatacount == self.emgSaveCount:
			self.emgData = pd.DataFrame(self.emgData) #the type of self.emgData element is class 'numpy.float64'
			with open(self.emgFileName ,'a+') as f:
				self.emgData.to_csv(f , header=0)
			self.emgDatacount = 0
			self.emgData=[]
			
	def creatImuDataFile(self):
		if self.imuDatacount == self.imuSaveCount:
			self.imuData = pd.DataFrame(self.imuData) #the type of self.emgData element is class 'numpy.float64'
			with open(self.imuFileName ,'a+') as f:
				self.imuData.to_csv(f , header=0)
			self.imuDatacount = 0
			self.imuData=[]

	def set_channel_range(self , channel_range):

		if "emg" in self.devType:
			self.emgDev.set_channel_range(channel_range)
		if "acc" in self.devType:
			self.accDev.set_channel_range(channel_range)

		self.channel_range = channel_range
		self.channel_number = len(channel_range)

	def getChannelName(self):

		for channelNum in self.channel_range:
			tempStr = "ch" + str(channelNum)
			self.channelStrList.append(tempStr)
		self.channelStrList.append("label")

	def setTheIndex(self):
		if "emg" in self.devType:
			self.emgFileName = self.dataFilePath + 'delsys_emg.csv'
			self.emgData = pd.DataFrame(self.emgData ,  columns = self.channelStrList)
			with open(self.emgFileName ,'a+') as f:
				self.emgData.to_csv(f )
			self.emgData = []
		if "acc" in self.devType:
			self.imuFileName = self.dataFilePath + 'delsys_imu.csv'
			self.imuData = pd.DataFrame(self.imuData ,  columns = self.channelStrList)
			with open(self.imuFileName ,'a+') as f:
				self.imuData.to_csv(f )
			self.imuData = []

	def emgRunMain(self):
		while True:
			self.readEmgData()
			self.createEmgDataFile()
			time.sleep(0.001)

	def accRunMain(self):
		while True:
			self.readImuData()
			self.creatImuDataFile()
			time.sleep(0.001)

	def run(self):

		if "emg" in self.devType:
			self.readEmgData()
			self.createEmgDataFile()	
		if "acc" in self.devType:
			self.readImuData()
			self.creatImuDataFile()

	def disconnect(self):
		print("Client stop.........")
		self.dataDev.stop()

if __name__ == '__main__':

	pass

		
