#conding:UTF-8
import socket
import struct
import numpy
import time 

'''
function  :Define the data that the client USES to receive the server
parameters:
	----------
    host : str
        IP address the TCU server is running on.
    cmd_port : int
        Port of TCU command messages.
    data_port : int
        Port of TCU data access.
    rate : int
        Sampling rate of the data source.
    total_channels : int
        Total number of channels supported by the device.
	-----------
attributes:
	----------
    BYTES_PER_CHANNEL : int
        Number of bytes per sample per channel. EMG and accelerometer data
    CMD_TERM : str
        Command string termination.
    CONNECTION_TIMEOUT : int
        Timeout for initializing connection to TCU (in seconds).
    ----------
notes    :
	----------
	Requires the Trigno Control Utility to be running
	Implementation details can be found in the Delsys SDK reference:
    http://www.delsys.com/integration/sdk/
	----------
'''
class _BaseTrignoDaq(object):
    
    BYTES_PER_CHANNEL = 4   #can be found in the SDK documentation
    CMD_TERM = '\r\n\r\n'
    CONNECTION_TIMEOUT = 2  #the uint is 's'

    def __init__(self, host, cmd_port, data_port, total_channels):

        self.host = host
        self.cmd_port = cmd_port
        self.data_port = data_port
        self.total_channels = total_channels

        self._min_recv_size = self.total_channels * self.BYTES_PER_CHANNEL

        self._initialize()


    def _initialize(self):

        # create command socket and consume the servers initial response
        self._comm_socket = socket.create_connection(
            (self.host, self.cmd_port), 2)
        self._comm_socket.recv(1024)
        # create the data socket
        self._data_socket = socket.create_connection(
            (self.host, self.data_port), 2)

    """
    Function:Tell the device to begin streaming data.
    Parameters:None
    Returns:None
    Note:
    	---------
    	You should call ``read()`` soon after this, though the device typically
    	takes about two seconds to send back the first batch of data.
    	---------
    """
    def start(self):
        self._send_cmd('START')

    """
    Function:
    	Request a sample of data from the device.
    Parameters:
	    ----------
	    num_samples : int
	        Number of samples to read per channel.
		----------
    Returns:
   	    ----------
    	data : ndarray, shape=(total_channels, num_samples)
        Data read from the device. Each channel is a row and each column
        is a point in time.
        ----------
    Note:
    	----------
    	This is a blocking method, meaning it returns only once the requested
    	number of samples are available.
    	----------
    """
    def read(self, num_samples):
        
        l_des = num_samples * self._min_recv_size
        l = 0
        packet = bytes()
        while l < l_des:
            try:
                packet += self._data_socket.recv(l_des - l)
            except socket.timeout:
                l = len(packet)
                packet += b'\x00' * (l_des - l)
                raise IOError("Device disconnected.")
            l = len(packet)
        # print("packet is :" , packet)
        data = numpy.asarray(
            struct.unpack('<'+'f'*self.total_channels*num_samples, packet))
        data = numpy.transpose(data.reshape((-1, self.total_channels)))
        return data

    """
    Function:Tell the device to stop streaming data.
    Parameters:None
    Returns:None
    Note:None
    """    
    def stop(self):
        self._send_cmd('STOP')

    """
    Function:Restart the connection to the Trigno Control Utility server.
    Parameters:None
    Returns:None
    Note:None
    """ 
    def reset(self):
        """"""
        self._initialize()

    def __del__(self):
        try:
            self._comm_socket.close()
        except:
            pass

    """
    Function:Send the commond to the Trigno Control Utility server.
    Parameters:None
    Returns:None
    Note:None
    """         
    def _send_cmd(self, command):
        self._comm_socket.send(self._cmd(command))
        resp = self._comm_socket.recv(128)
        self._validate(resp)

    @staticmethod
    def _cmd(command):
        return bytes("{}{}".format(command, _BaseTrignoDaq.CMD_TERM),
                     encoding='ascii')
    """
    Function:Check that the received reply command is correct.
    Parameters:None
    Returns:None
    Note:None
    """ 
    @staticmethod
    def _validate(response):
        s = str(response)
        if 'OK' not in s:
            print("warning: TrignoDaq command failed: {}".format(s))



"""
    Function:Get the emg data from server
    .
    Parameters:
    ----------
	    channel_range : tuple with 2 ints
	        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
	        channels lowchan through highchan. Each sensor has a single EMG
	        channel.
	    samples_per_read : int
	        Number of samples per channel to read in each read operation.
	    units : {'V', 'mV', 'normalized'}, optional
	        Units in which to return data. If 'V', the data is returned in its
	        un-scaled form (volts). If 'mV', the data is scaled to millivolt level.
	        If 'normalized', the data is scaled by its maximum level so that its
	        range is [-1, 1].
	    host : str, optional
	        IP address the TCU server is running on. By default, the device is
	        assumed to be attached to the local machine.
	    cmd_port : int, optional
	        Port of TCU command messages.
	    data_port : int, optional
	        Port of TCU EMG data access. By default, 50041 is used, but it is
	        configurable through the TCU graphical user interface.
    ----------
    Attributes:
    ----------
	    rate : int
	        Sampling rate in Hz.
	    scaler : float
	        Multiplicative scaling factor to convert the signals to the desired
	        units.
    ----------	
    Note:Requires the Trigno Control Utility to be running.
""" 
class TrignoEMG(_BaseTrignoDaq):

    def __init__(self, channel_range, samples_per_read, units='V',
                 host='localhost', cmd_port=50040, data_port=50041):
        super(TrignoEMG, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=16)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read
        self.num_channels = len(channel_range)

        self.rate = 2000  

        self.scaler = 1.
        if units == 'mV':
            self.scaler = 1000.
        elif units == 'normalized':
            # max range of EMG data is 11 mV
            self.scaler = 1 / 0.011

    """
    Function:Sets the number of channels to read from the device
    Parameters:channel_range : tuple
            Sensor channels to use (lowchan, highchan).
    Returns:None
    Note:None
    """ 
    def set_channel_range(self, channel_range):

        self.channel_range = channel_range
        self.num_channels = len(channel_range)
        return len(channel_range)

    """
    Function:Request a sample of data from the device.
    Parameters:channel_range : tuple
            Sensor channels to use (lowchan, highchan).
    Returns:data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
    Note:This is a blocking method, meaning it returns only once the requested
        number of samples are available.
    """ 
    def read(self):

        data = super(TrignoEMG, self).read(self.samples_per_read)
        tempList = numpy.ones((1,270)) * (time.time()) 
        tempData = []
        for i in self.channel_range:
            data1 = data[i - 1]
            tempData.extend(data1)
        data = numpy.asarray(tempData).reshape((self.num_channels,-1))
        # data = numpy.row_stack((data , tempList))   #the element of data is 'numpy.float64'
        return data

"""
    Function:Get the acc data from server
    .
    Parameters:
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan. Each sensor has three accelerometer
        channels.
    samples_per_read : int
        Number of samples per channel to read in each read operation.
    host : str, optional
        IP address the TCU server is running on. By default, the device is
        assumed to be attached to the local machine.
    cmd_port : int, optional
        Port of TCU command messages.
    data_port : int, optional
        Port of TCU accelerometer data access. By default, 50042 is used, but
        it is configurable through the TCU graphical user interface.
    ----------
    Attributes:
    ----------
	    rate : int
	        Sampling rate in Hz.
	    scaler : float
	        Multiplicative scaling factor to convert the signals to the desired
	        units.
    ----------	
    Note:Requires the Trigno Control Utility to be running.
""" 
class TrignoAccel(_BaseTrignoDaq):

    def __init__(self, channel_range, samples_per_read, host='localhost',
                 cmd_port=50040, data_port=50042):
        super(TrignoAccel, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=48)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read
        self.num_channels = len(channel_range)

        self.rate = 148.1

    """
    Function:Sets the number of channels to read from the device
    Parameters:channel_range : tuple
            Sensor channels to use (lowchan, highchan).
    Returns:None
    Note:None
    """ 
    def set_channel_range(self, channel_range):

        self.channel_range = channel_range
        self.num_channels = len(channel_range)
        return len(channel_range)

    """
    Function:Request a sample of data from the device.
    Parameters:channel_range : tuple
            Sensor channels to use (lowchan, highchan).
    Returns:data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
    Note:This is a blocking method, meaning it returns only once the requested
        number of samples are available.
    """ 
    def read(self):
        data = super(TrignoAccel, self).read(self.samples_per_read)
        tempList = numpy.ones((1,3*self.samples_per_read)) * (time.time()) 
        num = 0
        temp = []
        tempData = []
        for i in self.channel_range:
            xData = data[i - 1 + num]
            yData = data[i + num]
            zData = data[i + 1 + num]
            for j in range(len(xData)):
                temp.append(xData[j])
                temp.append(yData[j])
                temp.append(zData[j])
            tempData.extend(temp)
            temp = []
            num += 2
        data = numpy.asarray(tempData).reshape((self.num_channels,-1))
        data = numpy.row_stack((data , tempList))   #the element of data is 'numpy.float64'
        return data