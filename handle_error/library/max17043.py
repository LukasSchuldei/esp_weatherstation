from machine import I2C
import binascii

class max17043:
    REGISTER_VCELL = const(0X02)
    REGISTER_SOC = const(0X04)
    REGISTER_MODE = const(0X06)
    REGISTER_VERSION = const(0X08)
    REGISTER_CONFIG = const(0X0C)
    REGISTER_COMMAND = const(0XFE)

    def __init__(self, i2c, address=None):
        """
        Initialize the MAX17043 module and set the I2C interface
        """
        self.i2c = i2c
        if address is None:
            self.max17043Address = self.i2c.scan()[0]  # Scan and select the first available address
        else:
            self.max17043Address = address

    def __str__(self):
        """
        String representation of the values
        """
        rs  = "i2c address is {}\n".format( self.max17043Address )
        rs += "i2c pins are {}\n".format( self.i2c )
        rs += "version is {}\n".format( self.getVersion() )
        rs += "vcell is {} v\n".format( self.getVCell() )
        rs += "soc is {} %\n".format( self.getSoc() )
        rs += "compensatevalue is {}\n".format( self.getCompensateValue() )
        rs += "alert threshold is {} %\n".format( self.getAlertThreshold() )
        rs += "in alert is {}".format( self.inAlert() )
        return rs

    def address(self):
        """
        Return the i2c address
        """
        return self.max17043Address

    def reset(self):
        """
        Reset the MAX17043
        """
        self.__writeRegister(self.REGISTER_COMMAND, binascii.unhexlify('0054'))

    def getVCell(self):
        """
        Get the volts left in the cell
        """
        buf = self.__readRegister(self.REGISTER_VCELL)
        return (buf[0] << 4 | buf[1] >> 4) / 1000.0

    def getSoc(self):
        """
        Get the state of charge
        """
        buf = self.__readRegister(self.REGISTER_SOC)
        return (buf[0] + (buf[1] / 256.0))

    def getVersion(self):
        """
        Get the version of the max17043 module
        """
        buf = self.__readRegister(self.REGISTER_VERSION)
        return (buf[0] << 8) | (buf[1])

    def getCompensateValue(self):
        """
        Get the compensation value
        """
        return self.__readConfigRegister()[0]

    def getAlertThreshold(self):
        """
        Get the alert level
        """
        return (32 - (self.__readConfigRegister()[1] & 0x1f))

    def setAlertThreshold(self, threshold):
        """
        Sets the alert level
        """
        self.threshold = 32 - threshold if threshold < 32 else 32
        buf = self.__readConfigRegister()
        buf[1] = (buf[1] & 0xE0) | self.threshold
        self.__writeConfigRegister(buf)

    def inAlert(self):
        """
        Check if the max17043 module is in alert
        """
        return (self.__readConfigRegister())[1] & 0x20

    def clearAlert(self):
        """
        Clears the alert
        """
        self.__readConfigRegister()

    def quickStart(self):
        """
        Quick restart the MAX17043
        """
        self.__writeRegister(self.REGISTER_MODE, binascii.unhexlify('4000'))

    def __readRegister(self, address):
        """
        Reads the register at address, always returns bytearray of 2 char
        """
        return self.i2c.readfrom_mem(self.max17043Address, address, 2)

    def __readConfigRegister(self):
        """
        Read the config register, always returns bytearray of 2 char
        """
        return self.__readRegister(self.REGISTER_CONFIG)

    def __writeRegister(self, address, buf):
        """
        Write buf to the register address
        """
        self.i2c.writeto_mem(self.max17043Address, address, buf)

    def __writeConfigRegister(self, buf):
        """
        Write buf to the config register
        """
        self.__writeRegister(self.REGISTER_CONFIG, buf)

    def deinit(self):
        """
        Turn off the peripheral
        """
        self.i2c.deinit()
