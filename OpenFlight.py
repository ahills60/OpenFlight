import os, struct

class OpenFlight:
    """The OpenFlight is a base class that is capable of opening
       and extracting data from an OpenFlight database.
       
        Author: Andrew Hills
       Version: 0.0.1
    """
    
    def __init__(self, fileName = None):
        self._Checks = [self._check_filesize, self._check_header]
        self._ErrorMessages = ['This file does not conform to OpenFlight standards. The file size is not a multiple of 4.',
                               'This file does not conform to OpenFlight standards. The header is incorrect.']
        self._OpenFlightFormats = {11:   'Flight11',
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
        self.PrimaryNodeID = dict()
        self.Settings = dict()
    
    def _check_filesize(self, fileName):
        fileSize = os.stat(fileName).st_size
        
        if fileSize % 4 > 0:
            return False
        return True
    
    def _check_header(self, fileName):
        recognisableRecordTypes = [0x01]
        recognisableRecordSizes = [324]
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
        
        if recordLength != recognisableRecordSizes[recognised.index(True)]:
            raise Exception("Unexpected record length.")
        
        print "\rReading record name... ",
        
        self.DBName  = struct.unpack('>8s', self.f.read(8))[0]
        
        print "\rRead database name \"" + self.DBName + "\"\n"
        
        print "Determining file format revision number... ",
        iRead = struct.unpack('>i', self.f.read(4))[0]
        
        if iRead not in self._OpenFlightFormats:
            raise Exception("Unrecognised OpenFlight file format revision number.")
        print "\rDatabase is written in the " + self._OpenFlightFormats[iRead] + " file format.\n"
        
        # We're not interested in the edit revision number, so skip that:
        self.f.seek(4, os.SEEK_CUR)
        
        print "Determining date and time of last revision... ",
        
        # Next up is the date and time of the last revision
        iRead = struct.unpack('>32s', self.f.read(32))[0]
        
        print "\rRecorded date and time of last revision: " + iRead + "\n"
        
        print "Extracting Node ID numbers... ",
        
        self.PrimaryNodeID['Group'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['LOD'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['Object'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['Face'] = struct.unpack('>H', self.f.read(2))[0]
        
        print "\rValidating unit multiplier... ",
        
        iRead = struct.unpack('>H', self.f.read(2))[0]
        
        if iRead != 1:
            raise Exception("Unexpected value for unit multiplier.")
        
        print "\rExtracting scene settings... ",
        
        iRead = struct.unpack('>b', self.f.read(1))[0]
        
        Coords = {0: 'm', 1: 'km', 4: 'ft', 5: 'in', 8: 'nmi'}
        
        if iRead not in Coords:
            raise Exception("Could not interpret coordinate units.")
        
        self.Settings['Units'] = Coords[iRead]
        self.Settings['White'] = struct.unpack('>?', self.f.read(1))[0]
        self.Settings['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        
        # Skip some reserved area
        self.f.seek(24, os.SEEK_CUR)
        
        Projections = {0: 'Flat Earth', 1: "Trapezoidal", 2: "Round earth", 3: "Lambert", 4: "UTM", 5: "Geodetic", 6: "Geocentric"}
        
        iRead = struct.unpack('>i', self.f.read(4))[0]
        
        if iRead not in Projections:
            raise Exception ("Could not interpret projection type.")
        
        self.Settings['Projection'] = Projections[iRead]
        
        # Skip some reserved area
        self.f.seek(28, os.SEEK_CUR)
        
        self.PrimaryNodeID['DOF'] = struct.unpack('>H', self.f.read(2))[0]
        
        iRead = struct.unpack('>H', self.f.read(2))[0]
        
        if iRead != 1:
            raise Exception("Unexpected vertex storage type.")
        
        DBOrigin = {100: "OpenFlight", 200: "DIG I/DIG II", 300: "Evans and Sutherland CT5A/CT6", 400: "PSP DIG", 600: "General Electric CIV/CV/PT2000", 700: "Evans and Sutherland GDF"}
        
        self.DBOrigin = DBOrigin.get(struct.unpack('>i', self.f.read(4))[0], 'Unknown')
        
        self.Settings['DBCoords'] = dict()
        self.Settings['DBCoords']['SW-x'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['SW-y'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['Dx'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['Dy'] = struct.unpack('>d', self.f.read(8))[0]
        
        # Back to node IDs
        
        self.PrimaryNodeID['Sound'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['Path'] = struct.unpack('>H', self.f.read(2))[0]
        
        self.f.seek(8, os.SEEK_CUR)
        
        self.PrimaryNodeID['Clip'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['Text'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['BSP'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['Switch'] = struct.unpack('>H', self.f.read(2))[0]
        
        self.f.seek(4, os.SEEK_CUR)
        
        # Latitude and longitudes
        
        self.Settings['DBCoords']['SW-lat'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['SW-lon'] = struct.unpack('>d', self.f.read(8))[0]
        
        self.Settings['DBCoords']['NE-lat'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['NE-lon'] = struct.unpack('>d', self.f.read(8))[0]
        
        self.Settings['DBCoords']['Origin-lat'] = struct.unpack('>d', self.f.read(8))[0] 
        self.Settings['DBCoords']['Origin-long'] = struct.unpack('>d', self.f.read(8))[0]
        
        self.Settings['DBCoords']['Lambert-lat'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['Lambert-long'] = struct.unpack('>d', self.f.read(8))[0]
        
        # And back to node IDs
        
        self.PrimaryNodeID['LightS'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['LightP'] = struct.unpack('>H', self.f.read(2))[0]
        
        self.PrimaryNodeID['Road'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['CAT'] = struct.unpack('>H', self.f.read(2))[0]
        
        # Skip over some reserved parts:
        
        self.f.seek(8, os.SEEK_CUR)
        
        EllipsoidModel = {0: 'WGS 1984', 1: 'WGS 1972', 2: 'Bessel', 3: 'Clarke', 4: 'NAD 1927', -1: 'User defined ellipsoid'}
        
        iRead = struct.unpack('>I', self.f.read(4))[0]
        
        if iRead not in EllipsoidModel:
            raise Exception("Unexpected Earth ellipsoid model type")
        
        self.Settings['EllipsoidModel'] = EllipsoidModel[iRead]
        
        # More IDs
        
        self.PrimaryNodeID['Adaptive'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['Curve'] = struct.unpack('>H', self.f.read(2))[0]
        
        self.Settings['UTMZone'] = struct.unpack('>H', self.f.read(2))[0]
        
        self.f.seek(6, os.SEEK_CUR)
        
        self.Settings['DBCoords']['Dz'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['DBCoords']['Radius'] = struct.unpack('>d', self.f.read(8))[0]
        
        # More IDs
        self.PrimaryNodeID['Mesh'] = struct.unpack('>H', self.f.read(2))[0]
        self.PrimaryNodeID['LightPointSystem'] = struct.unpack('>H', self.f.read(2))[0]
        
        self.f.seek(4, os.SEEK_CUR)
        
        self.Settings['EarthMajor'] = struct.unpack('>d', self.f.read(8))[0]
        self.Settings['EarthMinor'] = struct.unpack('>d', self.f.read(8))[0]
        
        return True
        
    
    def isOpenFlight(self, fileName = None):
        
        # Number of checks to perform        
        if fileName is None:
            if self.fileName is None:
                raise IOError('No filename specified.')
            fileName = self.fileName
            
        if not os.path.exists(fileName):
            raise IOError('Could not find file.')
        
        checkList = [False] * len(self._Checks)
        
        try:
            for funcIdx, func in enumerate(self._Checks):
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
            messages = [message for msgIdx, message in enumerate(self._ErrorMessages) if not checkList[msgIdx]]
            for message in messages:
                print message
            print "\n"
            return False
        else:
            print "\nThis file conforms to OpenFlight standards\n"
            return True