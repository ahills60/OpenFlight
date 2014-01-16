import os, struct

class OpenFlight:
    """The OpenFlight is a base class that is capable of opening
       and extracting data from an OpenFlight database.
       
        Author: Andrew Hills
       Version: 0.0.1
    """
    
    def __init__(self, fileName = None):
        self.Checks = [self._check_filesize, self._check_header]
        self.ErrorMessages = ['This file does not conform to OpenFlight standards. The file size is not a multiple of 4.',
                              'This file does not conform to OpenFlight standards. The header is incorrect.']
        self.OpenFlightFormats = {11:   'Flight11',
                                  12:   'Flight12',
                                  14:   'OpenFlight v14.0 and v14.1',
                                  1420: 'OpenFlight v14.2',
                                  1510: 'OpenFlight v15.1',
                                  1540: 'OpenFlight v15.4',
                                  1550: 'OpenFlight v15.5',
                                  1560: 'OpenFlight v15.6',
                                  1570: 'OpenFlight v15.7',
                                  1580: 'OpenFlight v15.8',
                                  1600: 'OpenFlight v16.0',
                                  1610: 'OpenFlight v16.1',
                                  1620: 'OpenFlight v16.2',
                                  1630: 'OpenFlight v16.3',
                                  1640: 'OpenFlight v16.4'}
        self.fileName = fileName
        self.f = None
        self.DBName = ""
    
    def _check_filesize(self, fileName):
        fileSize = os.stat(fileName).st_size
        
        if fileSize % 4 > 0:
            return False
        return True
    
    def _check_header(self, fileName):
        recognisableRecordTypes = [0x01]
        if self.f is None:
            self.f = open(fileName, 'rb')
        # Ensure we're at the start of the file
        self.f.seek(0)
        
        print "Determining record type... ",
        iRead = struct.unpack('>h', self.f.read(2))[0]
        
        recognised = [iRead == this for this in recognisableRecordTypes]
        
        if not any(recognised):
            raise Exception("Unidentifiable record type")
        
        print "\rDetermining record length... ",
        recordLength = struct.unpack('>H', self.f.read(2))[0]
        
        if recordLength != 324:
            raise Exception("Unexpected record length.")
        
        print "\rReading record name... ",
        
        self.DBName  = struct.unpack('>8s', self.f.read(8))[0]
        
        print "\rRead database name \"" + self.DBName + "\"\n"
        
        print "Determining file format revision number... ",
        iRead = struct.unpack('>i', self.f.read(4))[0]
        
        if iRead not in self.OpenFlightFormats:
            raise Exception("Unrecognised OpenFlight file format revision number.")
        print "\rDatabase is written in the " + self.OpenFlightFormats[iRead] + " file format.\n"
        
        # We're not interested in the edit revision number, so skip that:
        self.f.seek(4, os.SEEK_CUR)
        
        return True
        
    
    def isOpenFlight(self, fileName = None):
        
        # Number of checks to perform        
        if fileName is None:
            if self.fileName is None:
                raise IOError('No filename specified.')
            fileName = self.fileName
            
        if not os.path.exists(fileName):
            raise IOError('Could not find file.')
        
        checkList = [False] * len(self.Checks)
        
        try:
            for funcIdx, func in enumerate(self.Checks):
                checkList[funcIdx] = func(fileName)
        except BaseException, e:
            print("An error occurred when calling " + str(func) + ".")
            print(str(e))
        finally:
            if self.f is not None:
                self.f.close()
                self.f = None
        
        if not all(checkList):
            print "\nThe following errors were encountered:\n"
            messages = [message for msgIdx, message in enumerate(self.ErrorMessages) if not checkList[msgIdx]]
            for message in messages:
                print message
            print "\n"
            return False
        else:
            print "\nThis file conforms to OpenFlight standards\n"
            return True