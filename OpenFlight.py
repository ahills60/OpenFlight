import os, struct
import numpy as np

class OpenFlight:
    """The OpenFlight is a base class that is capable of opening
       and extracting data from an OpenFlight database.
       
        Author: Andrew Hills
       Version: 0.0.1
    """
    
    def __init__(self, fileName = None, verbose = False, parent = None, tabbing = 0, skip_missing_textures = False):
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
        self._LastPlace = None
        # The tuple order for OpCodes is (op_function, size, friendly name)
        self._OpCodes = {   0:    (self._opReserved, None, 'padding'),
                            1:    (self._opHeader, 324, 'header'),
                            2:    (self._opGroup, 44, 'group'),
                            4:    (self._opObject, 28, 'object'),
                            5:    (self._opFace, 80, 'face'),
                           10:    (self._opPush, 4, 'push'),
                           11:    (self._opPop, 4, 'pop'),
                           14:    (self._opDoF, 384, 'degree of freedom'),
                           19:    (self._opPushSubface, 4, 'push subface'),
                           20:    (self._opPopSubface, 4, 'pop subface'),
                           21:    (self._opPushExtension, 24, 'push extension'),
                           22:    (self._opPopExtension, 24, 'pop extension'),
                           23:    (self._opContinuation, None, 'continuation'),
                           31:    (self._opComment, None, 'comment'),
                           32:    (self._opColourPalette, None, 'colour palette'),
                           33:    (self._opLongID, None, 'long ID'),
                           49:    (self._opMatrix, 68, 'matrix'),
                           50:    (self._opVector, 16, 'vector'),
                           52:    (self._opMultitexture, None, 'multitexture'),
                           53:    (self._opUVList, 8, 'UV list'),
                           55:    (self._opBSP, 48, 'binary separating plane'),
                           60:    (self._opReplicate, 8, 'replicate'),
                           61:    (self._opInstRef, 8, 'instance reference'),
                           62:    (self._opInstDef, 8, 'instance definition'),
                           63:    (self._opExtRef, 216, 'external reference'),
                           64:    (self._opTexturePalette, 216, 'texture palette'),
                           67:    (self._opVertexPalette, 8, 'vertex palette'),
                           68:    (self._opVertexColour, 40, 'vertex with colour'),
                           69:    (self._opVertexColNorm, 56, 'vertex with colour and normal'),
                           70:    (self._opVertexColNormUV, 64, 'vertex with colour, normal and UV'),
                           71:    (self._opVertexColUV, 48, 'vertex with colour and UV'),
                           72:    (self._opVertexList, None, 'vertex list'),
                           73:    (self._opLoD, 80, 'level of detail'),
                           74:    (self._opBoundingBox, 52, 'bounding box'),
                           76:    (self._opRotEdge, 64, 'rotate about edge'),
                           78:    (self._opTranslate, 56, 'translate'),
                           79:    (self._opScale, 48, 'scale'),
                           80:    (self._opRotPoint, 48, 'rotate about point'),
                           81:    (self._opRotScPoint, 96, 'rotate and/or scale to point'),
                           82:    (self._opPut, 152, 'put'),
                           83:    (self._opEyeTrackPalette, 4008, 'eyepoint and trackplane palette'),
                           84:    (self._opMesh, 84, 'mesh'),
                           85:    (self._opLocVertexPool, None, 'local vertex pool'),
                           86:    (self._opMeshPrim, None, 'mesh primitive'),
                           87:    (self._opRoadSeg, 12, 'road segment'),
                           88:    (self._opRoadZone, 176, 'road zone'),
                           89:    (self._opMorphVertex, None, 'morph vertex list'),
                           90:    (self._opLinkPalette, None, 'linkage palette'),
                           91:    (self._opSound, 88, 'sound'),
                           92:    (self._opRoadPath, 632, 'road path'),
                           93:    (self._opSoundPalette, None, 'sound palette'),
                           94:    (self._opGenMatrix, 68, 'general matrix'),
                           95:    (self._opText, 320, 'text'),
                           96:    (self._opSwitch, None, 'switch'),
                           97:    (self._opLineStylePalette, 12, 'line style palette'),
                           98:    (self._opClipRegion, 280, 'clip region'),
                          100:    (self._opExtension, None, 'extension'),
                          101:    (self._opLightSrc, 64, 'light source'),
                          102:    (self._opLightSrcPalette, 240, 'light source palette'),
                          103:    (self._opReserved, None, 'reserved'),
                          104:    (self._opReserved, None, 'reserved'),
                          105:    (self._opBoundSphere, 16, 'bounding sphere'),
                          106:    (self._opBoundCylinder, 24, 'bounding cylinder'),
                          107:    (self._opBoundConvexHull, None, 'bounding convex hull'),
                          108:    (self._opBoundVolCentre, 32, 'bounding volume centre'),
                          109:    (self._opBoundVolOrientation, 32, 'bounding volume orientation'),
                          110:    (self._opReserved, None, 'reserved'),
                          111:    (self._opLightPt, 156, 'light point'),
                          112:    (self._opTextureMapPalette, None, 'texture mapping palette'),
                          113:    (self._opMatPalette, 84, 'material palette'),
                          114:    (self._opNameTable, None, 'name table'),
                          115:    (self._opCAT, 80, 'continuously adaptive terrain (CAT)'),
                          116:    (self._opCATData, None, 'CAT data'),
                          117:    (self._opReserved, None, 'reserved'),
                          118:    (self._opReserved, None, 'reserved'),
                          119:    (self._opBoundHist, None, 'bounding histogram'),
                          120:    (self._opReserved, None, 'reserved'),
                          121:    (self._opReserved, None, 'reserved'),
                          122:    (self._opPushAttr, 8, 'push attribute'),
                          123:    (self._opPopAttr, 4, 'pop attribute'),
                          124:    (self._opReserved, None, 'reserved'),
                          125:    (self._opReserved, None, 'reserved'),
                          126:    (self._opCurve, None, 'curve'),
                          127:    (self._opRoadConstruc, 168, 'road construction'),
                          128:    (self._opLightPtAppearPalette, 412, 'light point appearance palette'),
                          129:    (self._opLightPtAnimatPalette, None, 'light point animation palette'),
                          130:    (self._opIdxLightPt, 28, 'indexed light point'),
                          131:    (self._opLightPtSys, 24, 'light point system'),
                          132:    (self._opIdxStr, None, 'indexed string'),
                          133:    (self._opShaderPalette, None, 'shader palette'),
                          134:    (self._opReserved, None, 'reserved'),
                          135:    (self._opExtMatHdr, 28, 'extended material header'),
                          136:    (self._opExtMatAmb, 48, 'extended material ambient'),
                          137:    (self._opExtMatDif, 48, 'extended material diffuse'),
                          138:    (self._opExtMatSpc, 48, 'extended material specular'),
                          139:    (self._opExtMatEms, 48, 'extended material emissive'),
                          140:    (self._opExtMatAlp, 44, 'extended material alpha'),
                          141:    (self._opExtMatLightMap, 16, 'extended material light map'),
                          142:    (self._opExtMatNormMap, 12, 'extended material normal map'),
                          143:    (self._opExtMatBumpMap, 20, 'extended material bump map'),
                          144:    (self._opReserved, None, 'reserved'),
                          145:    (self._opExtMatShadowMap, 16, 'extended material shadow map'),
                          146:    (self._opReserved, None, 'reserved'),
                          147:    (self._opExtMatReflMap, 32, 'extended material reflection map'),
                          148:    (self._opExtGUIDPalette, 48, 'extension GUID palette'),
                          149:    (self._opExtFieldBool, 12, 'extension field boolean'),
                          150:    (self._opExtFieldInt, 12, 'extension field integer'),
                          151:    (self._opExtFieldFloat, 12, 'extension field float'),
                          152:    (self._opExtFieldDouble, 16, 'extension field double'),
                          153:    (self._opExtFieldString, None, 'extension field string'),
                          154:    (self._opExtFieldXMLString, None, 'extension field XML string record')}
        self._ObsoleteOpCodes = [3, 6, 7, 8, 9, 12, 13, 16, 17, 40, 41, 42, 43, 44, 45, 46, 47, 48, 51, 65, 66, 77]
        self._PreviousOpCode = 0
        
        self.Records = dict()
        self.Records["Tree"] = []
        self.Records["Instances"] = dict()
        self.Records["External"] = dict()
        self.Records["Vertices"] = dict()
        self.Records["VertexList"] = []
        self.Records["VertexUV"] = []
        self.Records["Textures"] = []
        self._RecordType = 'Tree'
        self._TreeStack = []
        self._InstanceStack = []
        self._Chunk = None
        self._verbose = verbose
        self._parent = parent
        self._tabbing = tabbing
        self._VertexCounter = 0
        self._TexturePatternIdx = None
        self.Records["TexturePatterns"] = []
        self._SkipMissingTextures = skip_missing_textures
        self.Records["Scale"] = []
        self.Records["Translate"] = []
        self._CurrentScale = np.ones((1, 3))
        self._CurrentTranslate = np.zeros((1, 3))
    
    def _readString(self, size, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:size]
            self._Chunk = self._Chunk[size:]
        else:
            data =  self.f.read(size)
        return struct.unpack('>' + str(size) + 's', data)[0].replace('\x00', '')
    
    def _readFloat(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:4]
            self._Chunk = self._Chunk[4:]
        else:
            data = self.f.read(4)
        return struct.unpack('>f', data)[0]
    
    def _readDouble(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:8]
            self._Chunk = self._Chunk[8:]
        else:
            data = self.f.read(8)
        return struct.unpack('>d', data)[0]
    
    def _readUShort(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:2]
            self._Chunk = self._Chunk[2:]
        else:
            data = self.f.read(2)
        return struct.unpack('>H', data)[0]
    
    def _readShort(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:2]
            self._Chunk = self._Chunk[2:]
        else:
            data = self.f.read(2)
        return struct.unpack('>h', data)[0]
    
    def _readUInt(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:4]
            self._Chunk = self._Chunk[4:]
        else:
            data = self.f.read(4)
        return struct.unpack('>I', data)[0]
    
    def _readInt(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:4]
            self._Chunk = self._Chunk[4:]
        else:
            data = self.f.read(4)
        return struct.unpack('>i', data)[0]
    
    def _readBool(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:1]
            self._Chunk = self._Chunk[1:]
        else:
            data = self.f.read(1)
        return struct.unpack('>?', data)[0]
    
    def _readUChar(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:1]
            self._Chunk = self._Chunk[1:]
        else:
            data = self.f.read(1)
        return struct.unpack('>B', data)[0]
    
    def _readSChar(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:1]
            self._Chunk = self._Chunk[1:]
        else:
            data = self.f.read(1)
        return struct.unpack('>b', data)[0]
    
    def _readChar(self, fromChunk = False):
        if fromChunk:
            data = self._Chunk[:1]
            self._Chunk = self._Chunk[1:]
        else:
            data = self.f.read(1)
        return struct.unpack('>c', data)[0]
    
    def _skip(self, noBytes, fromChunk = False):
        if fromChunk:
            self._Chunk = self._Chunk[noBytes:]
        else:
            self.f.seek(noBytes, os.SEEK_CUR)
    
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
        
        print '\t' * self._tabbing + "Determining record type... ",
        iRead = self._readShort()
        
        recognised = [iRead == this for this in recognisableRecordTypes]
        
        if not any(recognised):
            raise Exception("Unidentifiable record type")
        
        print "\r" + '\t' * self._tabbing + "Determining record length... ",
        recordLength = self._readUShort()
        
        # if recordLength != recognisableRecordSizes[recognised.index(True)]:
        #     raise Exception("Unexpected record length (%i)." % recordLength)
        
        print "\r" + '\t' * self._tabbing + "Reading record name... ",
        
        self.DBName  = self._readString(8)
        
        print "\r" + '\t' * self._tabbing + "Read database name \"" + self.DBName + "\"\n"
        
        print '\t' * self._tabbing + "Determining file format revision number... ",
        self._FileFormat = self._readInt()
        
        if self._FileFormat not in self._OpenFlightFormats:
            raise Exception("Unrecognised OpenFlight file format revision number.")
        print "\r" '\t' * self._tabbing + "Database is written in the " + self._OpenFlightFormats[self._FileFormat] + " file format.\n"
        
        # We're not interested in the edit revision number, so skip that:
        self._skip(4)
        
        print '\t' * self._tabbing + "Determining date and time of last revision... ",
        
        # Next up is the date and time of the last revision
        iRead = self._readString(32)
        
        print "\r" + '\t' * self._tabbing + "Recorded date and time of last revision: " + iRead + "\n"
        
        print '\t' * self._tabbing + "Extracting Node ID numbers... ",
        
        self.PrimaryNodeID['Group'] = self._readUShort()
        self.PrimaryNodeID['LOD'] = self._readUShort()
        self.PrimaryNodeID['Object'] = self._readUShort()
        self.PrimaryNodeID['Face'] = self._readUShort()
        
        print "\r" + '\t' * self._tabbing + "Validating unit multiplier... ",
        
        iRead = self._readUShort()
        
        if iRead != 1:
            raise Exception("Unexpected value for unit multiplier.")
        
        print "\r" + '\t' * self._tabbing + "Extracting scene settings... ",
        
        iRead = self._readUChar()
        
        Coords = {0: 'm', 1: 'km', 4: 'ft', 5: 'in', 8: 'nmi'}
        
        if iRead not in Coords:
            raise Exception("Could not interpret coordinate units.")
        
        self.Settings['Units'] = Coords[iRead]
        self.Settings['White'] = self._readBool()
        self.Settings['Flags'] = self._readUInt()
        
        # Skip some reserved area
        self._skip(24)
        
        Projections = {0: 'Flat Earth', 1: "Trapezoidal", 2: "Round earth", 3: "Lambert", 4: "UTM", 5: "Geodetic", 6: "Geocentric"}
        
        iRead = self._readInt()
        
        if iRead not in Projections:
            raise Exception ("Could not interpret projection type.")
        
        self.Settings['Projection'] = Projections[iRead]
        
        # Skip some reserved area
        self._skip(28)
        
        self.PrimaryNodeID['DOF'] = self._readUShort()
        
        iRead = self._readUShort()
        
        if iRead != 1:
            raise Exception("Unexpected vertex storage type.")
        
        DBOrigin = {100: "OpenFlight", 200: "DIG I/DIG II", 300: "Evans and Sutherland CT5A/CT6", 400: "PSP DIG", 600: "General Electric CIV/CV/PT2000", 700: "Evans and Sutherland GDF"}
        
        self.DBOrigin = DBOrigin.get(self._readInt(), 'Unknown')
        
        self.Settings['DBCoords'] = dict()
        self.Settings['DBCoords']['SW-x'] = self._readDouble()
        self.Settings['DBCoords']['SW-y'] = self._readDouble()
        self.Settings['DBCoords']['Dx'] = self._readDouble()
        self.Settings['DBCoords']['Dy'] = self._readDouble()
        
        # Back to node IDs
        
        self.PrimaryNodeID['Sound'] = self._readUShort()
        self.PrimaryNodeID['Path'] = self._readUShort()
        
        self._skip(8)
        
        self.PrimaryNodeID['Clip'] = self._readUShort()
        self.PrimaryNodeID['Text'] = self._readUShort()
        self.PrimaryNodeID['BSP'] = self._readUShort()
        self.PrimaryNodeID['Switch'] = self._readUShort()
        
        self._skip(4)
        
        # Latitude and longitudes
        
        self.Settings['DBCoords']['SW-lat'] = self._readDouble()
        self.Settings['DBCoords']['SW-lon'] = self._readDouble()
        
        self.Settings['DBCoords']['NE-lat'] = self._readDouble()
        self.Settings['DBCoords']['NE-lon'] = self._readDouble()
        
        self.Settings['DBCoords']['Origin-lat'] = self._readDouble() 
        self.Settings['DBCoords']['Origin-long'] = self._readDouble()
        
        self.Settings['DBCoords']['Lambert-lat'] = self._readDouble()
        self.Settings['DBCoords']['Lambert-long'] = self._readDouble()
        
        # And back to node IDs
        
        self.PrimaryNodeID['LightS'] = self._readUShort()
        self.PrimaryNodeID['LightP'] = self._readUShort()
        
        self.PrimaryNodeID['Road'] = self._readUShort()
        self.PrimaryNodeID['CAT'] = self._readUShort()
        
        # Skip over some reserved parts:
        
        self._skip(8)
        
        EllipsoidModel = {0: 'WGS 1984', 1: 'WGS 1972', 2: 'Bessel', 3: 'Clarke', 4: 'NAD 1927', -1: 'User defined ellipsoid'}
        
        iRead = self._readInt()
        
        if iRead not in EllipsoidModel:
            raise Exception("Unexpected Earth ellipsoid model type")
        
        self.Settings['EllipsoidModel'] = EllipsoidModel[iRead]
        
        # More IDs
        
        self.PrimaryNodeID['Adaptive'] = self._readUShort()
        self.PrimaryNodeID['Curve'] = self._readUShort()
        
        if self._FileFormat >= 1580:
            # From 15.8, the file format has been consistent
            self.Settings['UTMZone'] = self._readUShort()
        
            self._skip(6)
        
            self.Settings['DBCoords']['Dz'] = self._readDouble()
            self.Settings['DBCoords']['Radius'] = self._readDouble()
        
            # More IDs
            self.PrimaryNodeID['Mesh'] = self._readUShort()
            self.PrimaryNodeID['LightPointSystem'] = self._readUShort()
        
            self._skip(4)
        
            self.Settings['EarthMajor'] = self._readDouble()
            self.Settings['EarthMinor'] = self._readDouble()
        elif self._FileFormat >= 1550:
            # According to the specification, there should be 2 bytes of reserved space. If this is done, then
            # the header record is not a multiple of 4 bytes. An additional 4 byte skip loses record sync and
            # no skip seems to keep the records aligned.
            self._skip(0)
            
            # Update vertex record sizes:
            
            newSizes = {  2:    (self._opGroup, 32, 'group'),
                         69:    (self._opVertexColNorm, 52, 'vertex with colour and normal'),
                         70:    (self._opVertexColNormUV, 60, 'vertex with colour, normal and UV'),
                         79:    (self._opScale, 44, 'scale')}
            self._OpCodes.update(newSizes)
        
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
            self._LastPlace = self.f.tell()
        except BaseException, e:
            print('\t' * self._tabbing + "An error occurred when calling " + str(func) + ".")
            print('\t' * self._tabbing + str(e))
        finally:
            if self.f is not None:
                self.f.close()
                self.f = None
        
        if not all(checkList):
            print "\n" + '\t' * self._tabbing + "The following errors were encountered:\n"
            messages = [message for msgIdx, message in enumerate(self._ErrorMessages) if not checkList[msgIdx]]
            for message in messages:
                print '\t' * self._tabbing + message
            print "\n"
            return False
        else:
            print "\n" + '\t' * self._tabbing + "This file conforms to OpenFlight standards\n"
            return True
    
    def ReadFile(self, fileName = None):
        # Number of checks to perform
        if fileName is None:
            if self.fileName is None:
                raise IOError('No filename specified.')
            fileName = self.fileName
        
        print('\n' + '\t' * self._tabbing +  'File to open: ' + fileName + '\n')
        
        if not os.path.exists(fileName):
            raise IOError('Could not find file.')
        
        if self._LastPlace is None:
            if not self.isOpenFlight(fileName):
                raise Exception("Unable to continue. File does not conform to OpenFlight standards.")
        
        if self.f is None:
            self.f = open(fileName, 'rb')
        
        # We can skip past the header and start reading stuff...
        self.f.seek(self._LastPlace)
        
        # Reset the stacks
        self._TreeStack = []
        self._InstanceStack = []
        
        print '\t' * self._tabbing + "Reading OpenFlight file..."
        
        try:
            while True:
                iRead = self.f.read(2)
                if iRead == '':
                    break
                # There's some data.
                iRead = struct.unpack('>h', iRead)[0]
                if self._verbose:
                    print '\t' * self._tabbing + "Opcode read:", str(iRead)
                if iRead in self._ObsoleteOpCodes:
                    raise Exception("Unable to continue. File uses obsolete codes.")
                if iRead not in self._OpCodes:
                    raise Exception("Unable to continue OpenFlight Opcode not recognised.")
                # If here, there's a code that can be run.
                # Determine whether we should check the size of the block
                if self._OpCodes[iRead][1] is not None:
                    # There's a size we should check matches
                    RecordLength = self._readUShort()
                    if RecordLength != self._OpCodes[iRead][1]:
                        raise Exception("Unexpected " + self._OpCodes[iRead][2] + " record length")
                self._OpCodes[iRead][0]()
                
                # Lastly, save this Opcode:
                self._PreviousOpCode = iRead
            print '\t' * self._tabbing + "Finished reading", fileName + "\n"
        except BaseException, e:
            if iRead not in self._OpCodes:
                print('\t' * self._tabbing + "An error occurred when calling Opcode " + str(iRead) + ".")
            else:
                print('\t' * self._tabbing + "An error occurred when calling Opcode " + str(iRead) + " (" + self._OpCodes[iRead][2]  + ").")
            print(str(e))
            self.e = e
        finally:
            # Close nicely.
            if self.f is not None:
                self.f.close()
                self.f = None
    
    def _addObject(self, newObject = None):
        """
            Adds an object to the stack.
            An internal function.
        """
        if newObject is None:
            raise Exception("Unable to add object. No object was defined.")
        
        # Inject this object into the tree
        if self._RecordType == "Tree":
            node = self.Records["Tree"]
            for idx in self._TreeStack:
                node = node[idx]
            node.append(newObject)
        elif self._RecordType == "Instances":
            node = self.Records["Instances"]
            for idx in self._InstanceStack:
                node = node[idx]
            node.append(newObject)
        else:
            raise Exception("Record type not recognised.")
    
    def _opReserved(self):
        pass
    
    def _opHeader(self):
        # Opcode 1
        raise Exception("Another header found in file.")
    
    def _opGroup(self):
        # Opcode 2
        newObject = dict()
        
        newObject['Datatype'] = "Group"
        newObject['ASCIIID'] = self._readString(8)
        newObject['RelativePriority'] = self._readShort()
        
        # Skip some reserved spot
        self._skip(2)
        
        newObject['Flags'] = self._readUInt()
        newObject['FXID1'] = self._readShort()
        newObject['FXID2'] = self._readShort()
        newObject['Significance'] = self._readShort()
        newObject['LayerCode'] = self._readUChar()
        
        self._skip(5)
        
        if self._FileFormat >= 1580:
            newObject['LoopCount'] = self._readUInt()
            newObject['LoopDuration'] = self._readFloat()
            newObject['LastFrameDuration'] = self._readFloat()
        
        # Finally inject object into tree
        self._addObject(newObject)
    
    def _opObject(self):
        # Opcode 4
        newObject = dict()
        newObject['Datatype'] = "Object"
        newObject['ASCIIID'] = self._readString(8)
        newObject['Flags'] = self._readUInt()
        newObject['RelativePriority'] = self._readShort()
        newObject['Transparency'] = self._readUShort()
        newObject['FXID1'] = self._readShort()
        newObject['FXID2'] = self._readShort()
        newObject['Significance'] = self._readShort()
        self._skip(2)
        
        self._addObject(newObject)
    
    def _opFace(self):
        # Opcode 5
        newObject = dict()
        newObject['Datatype'] = "Face"
        newObject['ASCIIID'] = self._readString(8)
        newObject['IRColCode'] = self._readUInt()
        newObject['RelativePriority'] = self._readShort()
        
        newObject['DrawType'] = self._readUChar()
        
        drawTypes = [0, 1, 2, 3, 4, 8, 9, 10]
        if newObject['DrawType'] not in drawTypes:
            raise Exception("Unable to determine draw type.")
        
        newObject['TextureWhite'] = self._readBool()
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['AltColourNameIdx'] = self._readUShort()
        
        # Skip over reserved
        self._skip(1)
        
        templateTypes = [0, 1, 2, 4]
        newObject['Template'] = self._readUChar()
        if newObject['Template'] not in templateTypes:
            raise Exception("Unable to determine template type.")
        
        varNames = ['DetailTexturePatternIdx', 'TexturePatternIdx', 'MaterialIdx']
        
        for varName in varNames:
            newObject[varName] = self._readUShort()
            if newObject[varName] == -1:
                newObject[varName] = None
        
        # Save this variable for now. It can be collected by the vertex list command
        self._TexturePatternIdx = newObject['TexturePatternIdx']
        
        newObject['SurfaceMaterialCode'] = self._readShort()
        newObject['FeatureID'] = self._readShort()
        
        newObject['IRMaterialCode'] = self._readUInt()
        newObject['Transparency'] = self._readShort()
        newObject['LODGenerationControl'] = self._readUChar()
        newObject['LineStyleIdx'] = self._readUChar()
        
        newObject['Flags'] = self._readUInt()
        
        lightModes = [0, 1, 2, 3]
        newObject['LightMode'] = self._readUChar()
        if newObject['LightMode'] not in lightModes:
            raise Exception("Unable to determine light mode.")
        
        # Skip over reserved
        self._skip(7)
        
        newObject['PackedColour'] = self._readUInt()
        newObject['AltPackedColour'] = self._readUInt()
        
        newObject['TextureMappingIdx'] = self._readShort()
        if newObject['TextureMappingIdx'] == -1:
            newObject['TextureMappingIdx'] = None
        
        self._skip(2)
        
        newObject['PrimaryColourIdx'] = self._readUInt()
        if newObject['PrimaryColourIdx'] == -1:
            newObject['PrimaryColourIdx'] = None
        
        newObject['AltColourIdx'] = self._readUInt()
        if newObject['AltColourIdx'] == -1:
            newObject['AltColourIdx'] = None
        
        self._skip(2)
        
        newObject['ShaderIdx'] = self._readShort()
        if newObject['ShaderIdx'] == -1:
            newObject['ShaderIdx'] = None
        
        self._addObject(newObject)
    
    
    def _opPush(self):
        # Opcode 10
        if self._RecordType == "Tree":
            node = self.Records["Tree"]
            for idx in self._TreeStack:
                node = node[idx]
            self._TreeStack.append(len(node))
            node.append([])
        elif self._RecordType == "Instances":
            node = self.Records["Instances"]
            for idx in self._InstanceStack:
                node = node[idx]
            self._InstanceStack.append(len(node))
            node.append([])
        else:
            raise Exception("Unable to determine stack type.")
    
    def _opPop(self):
        # Opcode 11
        if self._RecordType == "Tree":
            if len(self._TreeStack) == 0:
                raise Exception("Tree stack is empty: nothing to pop.")
            self._TreeStack.pop()
        elif self._RecordType == "Instances":
            self._InstanceStack.pop()
            
            # If we pop enough times, we switch back to tree
            if len(self._InstanceStack) == 1:
                self._RecordType = "Tree"
                self._InstanceStack = []
        else:
            raise Exception("Unable to determine stack type.")
    
    def _opDoF(self):
        # Opcode 14
        newObject = dict()
        newObject['Datatype'] = 'DegreeOfFreedom'
        newObject['ASCIIID'] = self._readString(8)
        
        # Skip over a reserved area
        self._skip(4)
        
        varNames = ['DoFOrigin', 'DoFPointx', 'DoFPointxy']
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        varNames = ['z', 'y', 'x', 'pitch', 'roll', 'yaw', 'zScale', 'yScale', 'xScale']
        variants = ['Min', 'Max', 'Current', 'Increment']
        
        for varName in varNames:
            for variant in variants:
                newObject[varName + variant] = self._readDouble()
        
        # Flags
        newObject['Flags'] = self._readUInt()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    def _opPushSubface(self):
        # Opcode 19
        newObject = dict()
        newObject['Datatype'] = 'PushSubface'
        # Call the push command...
        self._opPush()
        # ... and add the push extension object
        self._addObject(newObject)
    
    
    def _opPopSubface(self):
        # Opcode 20
        newObject = dict()
        newObject['Datatype'] = 'PopSubface'
        # Add this object
        self._addObject(newObject)
        # before finally issuing a pop command
        self._opPop()
    
    
    def _opPushExtension(self):
        # Opcode 21
        newObject = dict()
        newObject['Datatype'] = 'PushExtension'
        self._skip(18)
        newObject['VertexRefIdx'] = self._readUShort()
        # Call the push command...
        self._opPush()
        # ... and add the push extension object
        self._addObject(newObject)
    
    
    def _opPopExtension(self):
        # Opcode 22
        newObject = dict()
        newObject['Datatype'] = 'PopExtension'
        self._skip(18)
        newObject['VertexRefIdx'] = self._readUShort()
        # Add this object
        self._addObject(newObject)
        # before finally issuing a pop command
        self._opPop()
    
    
    def _opContinuation(self):
        # Opcode 23
        # This function will require special handling as a continuation record extends previous records.
        raise Exception("Unexpected continuation record. This should have been handled by the " + self._OpCodes[self._PreviousOpCode][2] + " function.")
    
    
    def _opComment(self):
        # Opcode 31
        newObject = dict()
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        newObject['Datatype'] = 'Comment'
        
        # Read the string to the end of the chunk
        newObject['Text'] = self._readString(len(self._Chunk), fromChunk = True)
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opColourPalette(self):
        # Opcode 32
        
        # Read the record length
        RecordLength = self._readUShort()
        
        newObject = dict()
        newObject['Datatype'] = 'ColourPalette'
        
        # Skip a reserved area
        self._skip(128)
        
        newObject['BrightestRGB'] = np.zeros((1024, 1))
        for rowIdx in range(1024):
            newObject['BrightestRGB'][rowIdx, 0] = self._readUInt()
        
        if RecordLength > 4228:
            # Include colour names
            
            # Read the number of colour names:
            noNames = self._readUInt()
            
            newObject['ColourNames'] = dict()
            
            for colourIdx in range(noNames):
                nameLength = self._readUShort()
                self._skip(2)
                colIdx = self._readUShort()
                self._skip(2)
                newObject['ColourNames'][colIdx] = self._readString(RecordLength - 8)
        
        self._addObject(newObject)
    
    
    def _opLongID(self):
        # Opcode 33
        newObject = dict()
        newObject['Datatype'] = 'LongID'
        
        RecordLength = self._readUShort()
        
        newObject['ASCIIID'] = self._readString(RecordLength - 4)
        self._addObject(newObject)
    
    
    def _opMatrix(self):
        # Opcode 49        
        newObject = np.zeros((4, 4))
        for n in range(16):
            # Enter elements of a matrix by going across their columns
            newObject[int(n) / 4, n % 4] = self._readFloat()
        
        # Inject
        self._addObject(newObject)
    
    def _opVector(self):
        # Opcode 50
        newObject = dict()
        newObject['Datatype'] = 'Vector'
        
        Components = ['i', 'j', 'k']
        for component in Components:
            newObject[component] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opMultitexture(self):
        # Opcode 52
        RecordLength = self._readUShort()
        
        newObject = dict()
        newObject['Datatype'] = 'Multitexture'
        
        newObject['Mask'] = self._readUInt()
        
        varNames = ['TextureIndex', 'Effect', 'TextureMappingIndex', 'TextureData']
        for varName in varNames:
            newObject[varName] = []
        
        for textIdx in range((RecordLength / 8) - 1):
            for varName in varNames:
                newObject[varName].append(self._readUShort())
        
        self._addObject(newObject)
    
    def _opUVList(self):
        # Opcode 53
        newObject = dict()
        newObject['Datatype'] = 'UVList'
        
        RecordLength = self._readUShort()
        
        newObject['AttributeMask'] = self._readUInt()
        
        mask = 0x00000001
        
        flags = [False] * 7
        
        for idx in range(7):
            if newObject['AttributeMask'] & mask > 0:
                flags[idx] = True
            mask <<= 1
        
        Layers = ['Layer' + str(n + 1) for n in range(7) if flags[n]]
        
        varNames = ['U0', 'V0', 'U100', 'V100']
        
        for vertexIdx in range((RecordLength - 8) / (8 * len(Layers))):
            vertexName = 'Vertex' + str(vertexIdx)
            newObject[vertexName] = dict()
            for layer in Layers:
                newObject[vertexName][layer] = dict()
                for varName in varNames:
                    newObject[vertexName][layer][varName] = self._readFloat()
        
        # Finally, commit object to stack
        self._addObject(newObject)
    
    
    def _opBSP(self):
        # Opcode 55
        newObject = dict()
        newObject['Datatype'] = 'BinarySeparatingPlane'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['PlaneEquationCoeffs'] = np.zeros((1, 4))
        for colIdx in range(4):
            newObject['PlaneEquationCoeffs'][0, colIdx] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opReplicate(self):
        # Opcode 60
        newObject = dict()
        newObject['Datatype'] = 'Replicate'
        
        newObject['NoReplications'] = self._readUShort()
        
        # Skip over reserved space
        self._skip(2)
        
        self._addObject(newObject)
    
    
    def _opInstRef(self):
        # Opcode 61        
        # Read instance number
        instance = self._readUInt()
        
        if instance not in self.Records["Instances"]:
            raise Exception("Could not find an instance to reference")
        
        # Now add this object to the right place
        self._addObject(self.Records["Instances"][instance])
    
    
    def _opInstDef(self):
        # Opcode 62
        # Firstly, set the record type to instance definition
        self._RecordType = "Instances"
        
        # Read instance number
        instance = self._readUInt()
        
        if instance in self.Records["Instances"]:
            raise Exception("Instance definition number has already been declared.")
        
        # There are no problems. Create an instance and prepare to accept incoming data
        self.Records["Instances"][instance] = []
        self._InstanceStack.append(instance)
    
    def _opExtRef(self):
        # Opcode 63
        newObject = dict()
        newObject['Datatype'] = "ExternalReference"
        newObject['ASCIIPath'] = self._readString(200)
        
        self._skip(4)
        newObject["Flags"] = self._readUInt()
        newObject["BoundingBox"] = self._readUShort()
        self._skip(2)
        
        # Clean the pathname and make it usable for this system
        fileName = self._cleanExternalFilename(newObject['ASCIIPath'])
        
        # Check to see if this is the parent class:
        if self._parent is None:
            # Yes, this is the parent class
            if fileName not in self.Records['External']:
                # This has not been referenced before. 
                # Create a new instance of this class and read the file.
                extdb = OpenFlight(fileName, verbose = self._verbose, parent = self, tabbing = self._tabbing + 1)
                extdb.ReadFile()
                self.Records['External'][fileName] = extdb.Records
                extdb = None
        else:
            # This is a child class. Add this object to the parent class
            if fileName not in self._parent.Records['External']:
                # This has not been referenced before:
                # Create a new instance of this class and read the file.
                extdb = OpenFlight(fileName, verbose = self._verbose, parent = self._parent, tabbing = self._tabbing + 1)
                extdb.ReadFile()
                self._parent.Records['External'][filename] = extdb.Records
                extdb = None
        
        # Inject into tree
        self._addObject(newObject)
    
    def _opTexturePalette(self):
        # Opcode 64
        newObject = dict()
        newObject['Datatype'] = "TexturePalette"
        newObject['Filename'] = self._readString(200)
        newObject['TexturePatternIdx'] = self._readUInt()
        newObject['LocationInTexturePalette'] = np.zeros((1, 2))
        for colIdx in range(2):
            newObject['LocationInTexturePalette'][0, colIdx] = self._readUInt()
        
        # Check to see if this is the parent class
        if self._parent is None:
            # This is the parent class. Use the local records
            if newObject['Filename'] not in self.Records['External']:
                # This has not been referenced before.
                self.Records['External'][newObject['Filename']] = self._parseTextureFile(newObject['Filename'])
        else:
            # This is a child class. Add this object to the parent class
            if newObject['Filename'] not in self._parent.Records['External']:
                # This has not been referenced before:
                self._parent.Records['External'][newObject['Filename']] = self._parseTextureFile(newObject['Filename'])
        
        self._addObject(newObject)
        # Next append to the textures list.
        self.Records['Textures'].append(newObject)
    
    
    def _opVertexPalette(self):
        # Opcode 67
        newObject = dict()
        newObject['Datatype'] = "VertexPalette"
        newObject['Length'] = self._readUInt()
        
        self._addObject(newObject)
        self._VertexCounter += 8
    
    
    def _opVertexColour(self):
        # Opcode 68
        newObject = dict()
        newObject['Datatype'] = "VertexColour"
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['Flags'] = self._readUShort()
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = self._readDouble()
        
        newObject['PackedColour'] = self._readUInt()
        newObject['VertexColourIndex'] = self._readUInt()
        
        self._addObject(newObject)
        self.Records['Vertices'][self._VertexCounter] = newObject
        self.Records['VertexUV'].append(None)
        self._VertexCounter += 40
    
    
    def _opVertexColNorm(self):
        # Opcode 69
        newObject = dict()
        newObject['Datatype'] = "VertexColourWithNormal"
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['Flags'] = self._readUShort()
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = self._readDouble()
        newObject['Normal'] = np.zeros((1, 3))
        # For i, j and k
        for colIdx in range(3):
            newObject['Normal'][0, colIdx] = self._readFloat()
        
        newObject['PackedColour'] = self._readUInt()
        newObject['VertexColourIndex'] = self._readUInt()
        
        if self._FileFormat >= 1580:
            self._skip(4)
        
        self._addObject(newObject)
        self.Records['Vertices'][self._VertexCounter] = newObject
        self.Records['VertexUV'].append(None)
        # Retrieve record size from opcode list
        self._VertexCounter += self._OpCodes[69][1]
    
    
    def _opVertexColNormUV(self):
        # Opcode 70
        newObject = dict()
        newObject['Datatype'] = "VertexColourWithNormalUV"
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['Flags'] = self._readUShort()
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = self._readDouble()
        newObject['Normal'] = np.zeros((1, 3))
        # For i, j and k
        for colIdx in range(3):
            newObject['Normal'][0, colIdx] = self._readFloat()
        
        newObject['TextureCoordinate'] = np.zeros((1, 2))
        newObject['TextureCoordinate'][0, 0] = self._readFloat()
        newObject['TextureCoordinate'][0, 1] = self._readFloat()
        
        newObject['PackedColour'] = self._readUInt()
        newObject['VertexColourIndex'] = self._readUInt()
        
        if self._FileFormat >= 1580:
            self._skip(4)
        
        self._addObject(newObject)
        self.Records['Vertices'][self._VertexCounter] = newObject
        self.Records['VertexUV'].append(newObject['TextureCoordinate'])
        # Retrieve record size from opcode list
        self._VertexCounter += self._OpCodes[70][1]
    
    
    def _opVertexColUV(self):
        # Opcode 71
        newObject = dict()
        newObject['Datatype'] = "VertexColourWithUV"
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['Flags'] = self._readUShort()
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = self._readDouble()
        
        newObject['TextureCoordinate'] = np.zeros((1, 2))
        newObject['TextureCoordinate'][0, 0] = self._readFloat()
        newObject['TextureCoordinate'][0, 1] = self._readFloat()
        
        newObject['PackedColour'] = self._readUInt()
        newObject['VertexColourIndex'] = self._readUInt()
        
        self._addObject(newObject)
        self.Records['Vertices'][self._VertexCounter] = newObject
        self.Records['VertexUV'].append(newObject['TextureCoordinate'])
        self._VertexCounter += 48
    
    
    def _opVertexList(self):
        # Opcode 72
        newObject = dict()
        # Read the data to memory and extract data as normal with modified
        # read functions.
        self._readChunk()
        
        newObject['Datatype'] = "VertexList"
        RecordLength = len(self._Chunk)
        
        newObject['ByteOffset'] = []
        
        for verIdx in range((RecordLength / 4)):
            newObject['ByteOffset'].append(self._readUInt(fromChunk = True))
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
        
        # And keep a copy in the vertex list
        self.Records["VertexList"].append(newObject['ByteOffset'])
        self.Records["TexturePatterns"].append(self._TexturePatternIdx)
        self.Records["Scale"].append(self._CurrentScale)
        self.Records["Translate"].append(self._CurrentTranslate)
    
    
    def _opLoD(self):
        # Opcode 73
        newObject = dict()
        newObject['Datatype'] = 'LevelOfDetail'
        newObject['ASCIIID'] = self._readString(8)
        
        # Skip over the reserved area
        self.read.seek(4, os.SEEK_CUR)
        
        newObject['SwitchInDistance'] = self._readDouble()
        newObject['SwitchOutDistance'] = self._readDouble()
        
        newObject['FXID1'] = self._readShort()
        newObject['FXID2'] = self._readShort()
        
        newObject['Flags'] = self._readUInt()
        
        varNames = ['x', 'y', 'z']
        
        for varName in varNames:
            newObject[varName + 'Centre'] = self._readDouble()
        newObject['TransitionRange'] = self._readDouble()
        newObject['SignificantSize'] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opBoundingBox(self):
        # Opcode 74
        
        newObject = dict()
        newObject['Datatype'] = 'BoundingBox'
        
        # Skip over the reserved area
        self._skip(4)
        
        Positions = ['Lowest', 'Highest']
        Axes = ['x', 'y', 'z']
        
        for position in Positions:
            for axis in Axes:
                newObject[axis + position] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opRotEdge(self):
        # Opcode 76
        newObject = dict()
        newObject['Datatype'] = 'RotateAboutEdge'
        
        self._skip(4)
        
        varNames = ['FirstPoint', 'SecondPoint']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        newObject['Angle'] = self._readFloat()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opTranslate(self):
        # Opcode 78
        newObject = dict()
        newObject['Datatype'] = 'Translate'
        
        self._skip(4)
        
        varNames = ['From', 'Delta']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        self._CurrentTranslate = newObject['Delta']
        
        self._addObject(newObject)
    
    
    def _opScale(self):
        # Opcode 79
        newObject = dict()
        newObject['Datatype'] = 'Scale'
        
        self._skip(4)
        
        newObject['ScaleCentre'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['ScaleCentre'][0, colIdx] = self._readDouble()
        
        varNames = ['xScale', 'yScale', 'zScale']
        for colIdx, varName in enumerate(varNames):
            newObject[varName] = self._readFloat()
            self._CurrentScale[0, colIdx] = newObject[varName]
        
        if self._FileFormat >= 1580:
            self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opRotPoint(self):
        # Opcode 80
        newObject = dict()
        newObject['Datatype'] = 'RotateAboutPoint'
        
        self._skip(4)
        
        newObject['RotationCentre'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['RotationCentre'][0, colIdx] = self._readDouble()
        
        varNames = ['iAxis', 'jAxis', 'kAxis', 'Angle']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opRotScPoint(self):
        # Opcode 81
        newObject = dict()
        newObject['Datatype'] = 'RotateScaleToPoint'
        
        self._skip(4)
        
        varNames = ['ScaleCentre', 'ReferencePoint', 'ToPoint']
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        varNames = ['OverallScale', 'ScaleInDirection', 'Angle']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opPut(self):
        # Opcode 82
        newObject = dict()
        newObject['Datatype'] = 'Put'
        
        self._skip(4)
        
        varNames = ['FromOrigin', 'FromAlign', 'FromTrack', 'ToOrigin', 'ToAlign', 'ToTrack']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        self._addObject(newObject)
    
    def _opEyeTrackPalette(self):
        # Opcode 83
        newObject = dict()
        newObject['Datatype'] = 'EyepointAndTrackplanePalette'
        
        self._skip(4)
        
        for eyePointIdx in range(10):
            # Keep this simple
            eyePoint = 'EyePoint' + format(eyePointIdx, '02d')
            
            newObject[eyePoint] = dict()
            
            # Now the file
            newObject[eyePoint]['RotationCentre'] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[eyePoint]['RotationCentre'][0, colIdx] = self._readDouble()
            
            varNames = ['Yaw', 'Pitch', 'Roll']
            for varName in Varnames:
                newObject[eyePoint][varName] = self._readFloat()
            
            newObject[eyePoint]['RotationMatrix'] = np.zeros((4, 4))
            for n in range(16):
                # Enter elements of a matrix by going across their columns
                newObject[eyePoint]['RotationMatrix'][int(n) / 4, n % 4] = self._readFloat()
            
            varNames = ['FieldOfView', 'Scale', 'NearClippingPlane', 'FarClippingPlane']
            for varName in Varnames:
                newObject[eyePoint][varName] = self._readFloat()
            
            newObject[eyePoint]['FlythroughMatrix'] = np.zeros((4, 4))
            for n in range(16):
                # Enter elements of a matrix by going across their columns
                newObject[eyePoint]['FlythroughMatrix'][int(n) / 4, n % 4] = self._readFloat()
            
            newObject[eyePoint]['EyepointPosition'] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[eyePoint]['EyepointPosition'][0, colIdx] = self._readFloat()
            
            newObject[eyePoint]['YawFlythrough'] = self._readFloat()
            newObject[eyePoint]['PitchFlythrough'] = self._readFloat()
            
            newObject[eyePoint]['EyepointDirection'] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[eyePoint]['EyepointDirection'][0, colIdx] = self._readFloat()
            
            varNames = ['NoFlythrough', 'OrthoView', 'ValidEyepoint', 'xImageOffset', 'yImageOffset', 'ImageZoom']
            for varName in varNames:
                newObject[eyePoint][varName] = self._readInt()
            
            # Skip over 4*8 + 4 of reserved space
            self._skip(36)
        
        for trackplaneIdx in range(10):
            trackplane = 'Trackplane' + format(trackplaneIdx, '02d')
            
            newObject[trackplane] = dict()
            newObject[trackplane]['Valid'] = self._readInt()
            
            self._skip(4)
            
            varNames = ['Origin', 'Alignment', 'Plane']
            for varName in varNames:
                newObject[eyePoint][varName] = np.zeros((1, 3))
                for colIdx in range(3):
                    newObject[eyePoint][varName][0, colIdx] = self._readDouble()
            
            newObject[trackplane]['GridVisible'] = self._readBool()
            
            varNames = ['GridType', 'GridUnder']
            for varName in varNames:
                newObject[trackplane][varName] = self._readUChar()
            
            self._skip(1)
            
            newObject[trackplane]['GridAngle'] = self._readFloat()
            
            varNames = ['xGridSpace', 'yGridSpace']
            for varName in varNames:
                newObject[trackplane]['varName'] = self._readDouble()
            
            varNames = ['RadialGridDirection', 'RectangularGridDirection']
            for varName in varNames:
                newObject[trackplane][varName] = self._readSChar()
            
            newObject[trackplane]['SnapToGrid'] = self._readUChar()
            
            self._skip(2)
            
            newObject[trackplane]['GridSize'] = self._readDouble()
            
            # This may be incorrect. Record says a 4 byte boolean! I assume 4 * 1 byte booleans.
            for quadrant in range(1, 5):
                newObject[trackplane]['VisibleGridMask' + quadrant] = self._readBool()
            
            self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opMesh(self):
        # Opcode 84
        newObject = dict()
        newObject['Datatype'] = 'Mesh'
        
        # This is identical to the face record.
        
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['IRColourCode'] = self._readUInt()
        newObject['RelativePriority'] = self._readShort()
        
        newObject['DrawType'] = self._readUChar()
        
        drawTypes = [0, 1, 2, 3, 4, 8, 9, 10]
        if newObject['DrawType'] not in drawTypes:
            raise Exception("Unable to determine draw type.")
        
        newObject['TextureWhite'] = self._readBool()
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['AltColourNameIdx'] = self._readUShort()
        
        # Skip over reserved
        self._skip(1)
        
        templateTypes = [0, 1, 2, 4]
        newObject['Template'] = self._readUChar()
        if newObject['Template'] not in templateTypes:
            raise Exception("Unable to determine template type.")
        
        varNames = ['DetailTexturePatternIdx', 'TexturePatternIdx', 'MaterialIdx']
        
        for varName in varNames:
            newObject[varName] = self._readShort()
            if newObject[varName] == -1:
                newObject[varName] = None
        
        newObject['SurfaceMaterialCode'] = self._readShort()
        newObject['FeatureID'] = self._readShort()
        
        newObject['IRMaterialCode'] = self._readUInt()
        newObject['Transparency'] = self._readUShort()
        newObject['LODGenerationControl'] = self._readUChar()
        newObject['LineStyleIdx'] = self._readUChar()
        
        newObject['Flags'] = self._readUInt()
        
        lightModes = [0, 1, 2, 3]
        newObject['LightMode'] = self._readUChar()
        if newObject['LightMode'] not in lightModes:
            raise Exception("Unable to determine light mode.")
        
        # Skip over reserved
        self._skip(7)
        
        newObject['PackedColour'] = self._readUInt()
        newObject['AltPackedColour'] = self._readUInt()
        
        newObject['TextureMappingIdx'] = self._readShort()
        if newObject['TextureMappingIdx'] == -1:
            newObject['TextureMappingIdx'] = None
        
        self._skip(2)
        
        newObject['PrimaryColourIdx'] = self._readUInt()
        if newObject['PrimaryColourIdx'] == -1:
            newObject['PrimaryColourIdx'] = None
        
        newObject['AltColourIdx'] = self._readUInt()
        if newObject['AltColourIdx'] == -1:
            newObject['AltColourIdx'] = None
        
        self._skip(2)
        
        newObject['ShaderIdx'] = self._readShort()
        if newObject['ShaderIdx'] == -1:
            newObject['ShaderIdx'] = None
        
        self._addObject(newObject)
    
    
    def _opLocVertexPool(self):
        # Opcode 85
        newObject = dict()
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        
        newObject['Datatype'] = 'LocalVertexPool'
        newObject['NumberOfVertices'] = self._readUInt(fromChunk = True)
        newObject['AttributeMask'] = self._readUInt(fromChunk = True)
        
        mask = 0x01
        
        Flags = [False] * 12
        
        # Now process the attribute mask:
        for idx in range(12):
            if newObject['AttributeMask'] & mask > 0:
                Flags[idx] = True
            # Shift the mask left by one
            mask <<= 1
        
        if Flags[1] and Flags[2]:
            raise Exception("Unable to determine colour for vertex. Both colour index and RGBA colour are set.")
        
        varNames = ['UVBase']
        varNames.extend(['UV' + str(idx) for idx in range(1, 8)])
        
        # Now only take those variable names that have been enabled
        varNames = [filt[0] for filt in zip(varNames, Flags[4:]) if filt[1]]
        
        newObject['LocalVertexPool'] = []
        for idx in range(newObject['NumberOfVertices']):
            tempDict = dict()
            
            if Flags[0]:
                tempDict['Coordinate'] = np.zeros((1, 3))
                for colIdx in range(3):
                    tempDict['Coordinate'][0, colIdx] = self._readDouble(fromChunk = True)
            if Flags[1] or Flags[2]:
                # Whilst the flags mean different things, they have similar construction
                tempDict['Colour'] = np.zeros((1, 4))
                for colIdx in range(4):
                    tempDict['Colour'][0, colIdx] = self._readUChar(fromChunk = True)
            if Flags[3]:
                tempDict['Normal'] = np.zeros((1, 3))
                for colIdx in range(3):
                    tempDict['Normal'][0, colIdx] = self._readFloat(fromChunk = True)
            for varName in varNames:
                tempDict[varName] = np.zeros((1, 2))
                for colIdx in range(2):
                    tempDict[varName][0, colIdx] = self._readFloat(fromChunk = True)
            
            newObject['LocalVertexPool'].append(tempDict)
        
        tempDict = None
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opMeshPrim(self):
        # Opcode 86
        newObject = dict()
        newObject['Datatype'] = 'MeshPrimitive'
        
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        
        newObject['PrimitiveType'] = self._readShort(fromChunk = True)
        indexSize = self._readUShort(fromChunk = True)
        
        if indexSize not in [1, 2, 4]:
            raise Exception("Unable to determine the index size.")
        
        functions = {1: self._readSChar, 2: self._readShort, 4: self._readInt}
        
        readFunction = functions[indexSize]
        
        newObject['VertexCount'] = self._readUInt(fromChunk = True)
        
        newObject['VertexIndex'] = []
        
        for idx in range(newObject['VertexCount']):
            newObject['VertexIndex'].append(readFunction(fromChunk = True))
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opRoadSeg(self):
        # Opcode 87
        newObject = dict()
        newObject['Datatype'] = "RoadSegment"
        newObject['ASCIIID'] = self._readString(8)
        
        self._addObject(newObject)
    
    
    def _opRoadZone(self):
        # Opcode 88
        newObject = dict()
        newObject['Datatype'] = 'RoadZone'
        newObject['ZoneFilename'] = self._readString(120)
        
        self._skip(4)
        
        varNames = ['LowerLeft', 'UpperRight']
        coordTypes = ['x', 'y']
        
        for varName in varNames:
            for coordType in coordTypes:
                newObject[coordType + varName] = self._readDouble()
        newObject['GridInterval'] = self._readDouble()
        newObject['NoPostsX'] = self._readUInt()
        newObject['NoPostsY'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opMorphVertex(self):
        # Opcode 89
        newObject = dict()
        newObject['Datatype'] = 'MorphVertexList'
        
        # Read the data to memory and extract data as normal with modified
        # read fucntions
        self._readChunk()
        
        newObject['Offset0'] = []
        newObject['Offset100'] = []
        
        for idx in range(len(self._Chunk) / 8):
            newObject['Offset0'].append(self._readInt(fromChunk = True))
            newObject['Offset100'].append(self._readInt(fromChunk = True))
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opLinkPalette(self):
        # Opcode 90
        newObject = dict()
        newObject['Datatype'] = 'LinkagePalette'
        
        RecordLength = self._readUShort()
        
        # Next read the subtype
        subtype = self._readInt()
        
        if subtype == 1:
            newObject['Subtype'] = 'KeyTableHeader'
            
            varNames = ['MaxNumber', 'ActualNumber', 'TotalLength']
            for varName in varNames:
                newObject[varName] = self._readInt()
            
            # Skip over the reserved area:
            self._skip(12)
            
            newObject['Records'] = []
            
            varNames = ['KeyValue', 'KeyDatatype', 'DataOffset']
            
            for idx in range(newObject['ActualNumber']):
                tempDict = dict()
                for varName in varNames:
                    tempDict[varName] = self._readInt()
                if varName['KeyDatatype'] not in [0x12120001, 0x12120002, 0x12120004]:
                    raise Exception('Unable to determine data type for record ' + str(idx))
                # Append this record to the record list:
                newObject.append(varName)
        if subtype == 2:
            newObject['Subtype'] = 'KeyDataRecord'
            newObject['DataLength'] = self._readInt()
            newobject['PackedData'] = self.f.read(RecordLength - 12)
        
        # Finally, add this object to the stack:
        self._addObject(newObject)
    
    
    def _opSound(self):
        # Opcode 91
        newObject = dict()
        newObject['Datatype'] = 'Sound'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['IndexIntoSoundPalette'] = self._readUInt()
        
        self._skip(4)
        
        newObject['OffsetCoordinate'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['OffsetCoordinate'][0, colIdx] = self._readDouble()
        
        newObject['SoundDirection'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['SoundDirection'][0, colIdx] = self._readFloat()
        
        varNames = ['Amplitude', 'PitchBend', 'Priority', 'Falloff', 'Width']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        newObject['Flags'] = self._readUInt()
        
        # Skip over reserved space
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opRoadPath(self):
        # Opcode 92
        newObject = dict()
        newObject['Datatype'] = 'RoadPath'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['PathName'] = self._readString(120)
        
        newObject['SpeedLimit'] = self._readDouble()
        
        # No passing should be a *4 byte* boolean. I will read this as an integer instead.
        newObject['NoPassing'] = self._readUInt()
        
        newObject['VertexType'] = self._readUInt()
        if newObject['VertexType'] not in [1, 2]:
            raise Exception("Unable to determine vertex type.")
        
        self._skip(480)
        
        self._addObject(newObject)
    
    
    def _opSoundPalette(self):
        # Opcode 93
        newObject = dict()
        newObject['Datatype'] = 'SoundPaletteData'
        
        RecordLength = self._readUShort()
        
        # This can be of two types based on the subtype value:
        Subtype = self._readUInt()
        
        if Subtype == 1:
            # This is a sound palette header record
            newObject['Subtype'] = "Header"
            varNames = ['MaxNumber', 'ActualNumber']
            for varName in varNames:
                newObject[varName] = self._readUInt()
            
            # Skip over reserved area
            self._skip(12)
            
            for soundNo in range(newObject['ActualNumber']):
                SoundName = "Sound" + str(soundNo)
                newObject[SoundName] = dict()
                newObject[SoundName]['SoundIndex'] = self._readUInt()
                # Reserved space for this entry
                self._skip(4)
                newObject[SoundName]['FilenameOffset'] = self._readUInt()
        elif Subtype == 2:
            # This is a sound palette data record
            newObject['Subtype'] = "Data"
            newObject['TotalLength'] = self._readUInt()
            newObject['PackedFilenames'] = self._readString(RecordLength - 12)
        else:
            # This is not recognised.
            raise Exception("Unable to determine sound record subtype.")
        
        self._addObject(newObject)
    
    def _opGenMatrix(self):
        # Opcode 94
        # This is the same as the matrix command, so call the matrix function
        self._opMatrix(fileName)
    
    
    def _opText(self):
        # Opcode 95
        newObject = dict()
        newObject['Datatype'] = 'Text'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(8)
        
        newObject['Type'] = self._readUInt()
        if newObject['Type'] not in [-1, 0, 1, 2]:
            raise Exception("Unable to determine type.")
        
        newObject['DrawType'] = self._readUInt()
        if newObject['DrawType'] not in [0, 1, 2, 3]:
            raise Exception("Unable to determine draw type.")
        
        newObject['Justification'] = self._readUInt()
        if newObject['Justification'] not in [-1, 0, 1, 2]:
            raise Exception("Unable to determine justification.")
        
        newObject['FloatingPointValue'] = self._readDouble()
        newObject['IntegerValue'] = self._readInt()
        
        self._skip(20)
        
        varNames = ['Flags', 'Colour', 'Colour2', 'Material', None, 'MaxLines', 'MaxCharacters', 'CurrentLength', 'NextLineNumber', 'LineNumberAtTop', 'LowInteger', 'HighInteger']
        for varName in varNames:
            if varNames is None:
                self._skip(4)
            else:
                newObject[varName] = self._readUInt()
        
        newObject['LowFloat'] = self._readDouble()
        newObject['HighFloat'] = self._readDouble()
        
        varNames = ['LowerLeftCorner', 'UpperRightCorner']
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        newObject['FontName'] = self._readString(120)
        
        varNames = ['DrawVertical', 'DrawItalic', 'DrawBold', 'DrawUnderline', 'LineStyle']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opSwitch(self):
        # Opcode 96
        newObject = dict()
        newObject['Datatype'] = 'Switch'
        
        RecordLength = self._readUShort()
        
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        varNames = ['CurrentMask', 'NumberOfMasks', 'NumberOfWordsPerMask']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        newObject['MaskWords'] = []
        for idx in range(varNames['NumberOfMasks'] * varNames['NumberOfWordsPerMask']):
            newObject['MaskWords'].append(self._readUInt())
        
        self._addObject(newObject)
    
    
    def _opLineStylePalette(self):
        # Opcode 97
        newObject = dict()
        newObject['Datatype'] = 'LineStylePalette'
        newObject['LineStyleIdx'] = self._readUShort()
        newObject['PatternMask'] = self._readUShort()
        newObject['LineWidth'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opClipRegion(self):
        # Opcode 98
        newObject = dict()
        newObject['Datatype'] = 'ClipRegion'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(6)
        
        newObject['Flags'] = []
        for flagNo in range(5):
            newObject['Flags'].append(self._readChar())
        
        self._skip(1)
        
        for regionIdx in range(1, 5):
            newObject['Region' + str(regionIdx)] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject['Region' + str(regionIdx)][0, colIdx] = self._readDouble()
        
        varNames = ['CoeffsA', 'CoeffsB', 'CoeffsC', 'CoeffsD']
        
        for varName in varNames:
            newObject[varName] = []
            for colIdx in range(5):
                newObject[varName].append(struct.unpack('>d', self.f.read(8))[0])
        
        self._addObject(newObject)
    
    
    def _opExtension(self):
        # Opcode 100
        newObject = dict()
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        newObject['Datatype'] = 'Extension'
        
        varNames = ['ASCIIID', 'SiteID']
        for varName in varNames:
            newObject[varName] = self._readString(8, fromChunk = True)
        
        self._skip(1, fromChunk = True)
        
        newObject['Revision'] = self._readSChar(fromChunk = True)
        newObject['RecordCode'] = self._readUShort(fromChunk = True)
        
        newObject['ExtendedData'] = self._readString(len(self._Chunk), fromChunk = True)
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opLightSrc(self):
        # Opcode 101
        newObject = dict()
        newObject['Datatype'] = 'LightSource'
        
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['IndexIntoLightPalette'] = self._readUInt()
        
        self._skip(4)
        
        newObject['Flags'] = self._readUInt()
        
        self._skip(4)
        
        newObject['Position'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['Position'][0, colIdx] = self._readDouble()
        
        varNames = ['Yaw', 'Pitch']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opLightSrcPalette(self):
        # Opcode 102
        newObject = dict()
        newObject['Datatype'] = 'LightSourcePalette'
        newObject['LightSourceIndex'] = self._readUInt()
        
        self._skip(8)
        
        newObject['LightSourceName'] = self._readString(20)
        
        self._skip(4)
        
        varNames = ['Ambient', 'Diffuse', 'Specular']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 4))
            for colIdx in range(4):
                newObject[varName][0, colIdx] = self._readFloat()
        
        newObject['LightingType'] = self._readUInt()
        if newObject['LightingType'] not in [0, 1, 2]:
            raise Exception("Unable to determine lighting type.")
        
        self._skip(40)
        
        varNames = ['SpotExponentialDropoffTerm', 'SpotCutoffAngle', 'Yaw', 'Pitch', 'ConstantAttenuationCoeff', 'LinearAttenuationCoeff', 'QuadraticAttenuationCoeff']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        newObject['ModellingLight'] = self._readUInt()
        if newObject['ModellingLight'] not in [0, 1]:
            raise Exception("Unable to determine modelling light.")
        
        # Skip over reserved area.
        self._skip(76)
        
        self._addObject(newObject)
    
    
    def _opBoundSphere(self):
        # Opcode 105
        newObject = dict()
        newObject['Datatype'] = 'BoundingSphere'
        
        # Skip over the reserved area
        self._skip(4)
        
        newObject['Radius'] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundCylinder(self):
        # Opcode 106
        newObject = dict()
        newObject['Datatype'] = 'BoundingCylinder'
        
        # Skip over the reserved area
        self._skip(4)
        
        newObject['Radius'] = self._readDouble()
        newObject['Height'] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundConvexHull(self):
        # Opcode 107
        newObject = dict()
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        
        newObject['Datatype'] = 'BoundingConvexHull'
        
        newObject['NumberOfTriangles'] = self._readUInt(fromChunk = True)
        
        newObject['Vertex1'] = []
        newObject['Vertex2'] = []
        newObject['Vertex3'] = []
        
        RecordLength = len(self._Chunk)
        
        # Read the vertex records:
        for triangleIdx in range(RecordLength / 8):
            for vertexIdx in range(1, 4):
                # Represent x, y and z
                tempVector = np.zeros((1, 3))
                for colIdx in range(3):
                    tempVector[0, colIdx] = self._readDouble(fromChunk = True)
                # Add this to the appropriate vector index
                newObject['Vertex' + str(vertexIdx)].append(tempVector)
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opBoundVolCentre(self):
        # Opcode 108
        newObject = dict()
        newObject['Datatype'] = 'BoundingVolumeCentre'
        
        # Skip over the reserved area
        self._skip(4)
        
        Axes = ['x', 'y', 'z']
        
        for axis in Axes:
            newObject[axis] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundVolOrientation(self):
        # Opcode 109
        newObject = dict()
        newObject['Datatype'] = 'BoundingVolumeOrientation'
        
        # Skip over the reserved area
        self._skip(4)
        
        Angles = ['Yaw', 'Pitch', 'Roll']
        
        for angle in Angles:
            newObject[angle] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    def _opLightPt(self):
        # Opcode 111
        newObject = dict()
        newObject['Datatype'] = 'LightPoint'
        newObject['ASCIIID'] = self._readString(8)
        
        varNames = ['SurfaceMaterialCode', 'FeatureID']
        for varName in varNames:
            newObject[varName] = self._readUShort()
        
        varNames = ['BackColourBiDir', 'DisplayMode']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        # DisplayMode can only take a few values
        if newObject['DisplayMode'] not in [0, 1, 2]:
            raise Exception("Unable to determine display mode.")
        
        varNames = ['Intensity', 'BackIntensity', 'MinimumDefocus', 'MaximumDefocus']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        varNames = [('FadingMode', 'fading mode'), ('FogPunchMode', 'fog punch mode'), ('DirectionalMode', 'directional mode'), ('RangeMode', 'range mode')]
        
        for varName in varNames:
            newObject[varName[0]] = self._readUInt()
            if newObject[varName[0]] not in [0, 1]:
                raise Exception("Unable to determine " + varName[1] + ".")
        
        varNames = ['MinPixelSize', 'MaxPixelSize', 'ActualSize', 'TransparentFalloffPixelSize', 'TransparentFalloffExponent', 'TransparentFalloffScalar', 'TransparentFalloffClamp', 'FogScalar', None, 'SizeDifferenceThreshold']
        
        for varName in varNames:
            # Skip over reserved space
            if varName is None:
                self._skip(4)
            else:
                newObject[varName] = self._readFloat()
        
        newObject['Directionality'] = self._readUInt()
        if newObject['Directionality'] not in [0, 1, 2]:
            raise Exception("Unable to determine directionality.")
        
        varNames = ['HorizontalLobeAngle', 'VerticalLobeAngle', 'LobeRollAngle', 'DirectionalFalloffExponent', 'DirectionalAmbientIntensity', 'AnimationPeriod', 'AnimationPhaseDelay', 'AnimationEnabledPeriod', 'Significance']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        newObject['CalligraphicDrawOrder'] = self._readInt()
        
        newObject['Flags'] = self._readUInt()
        
        newObject['AxisOfRotation'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['AxisOfRotation'][0, colIdx] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opTextureMapPalette(self):
        # Opcode 112
        newObject = dict()
        newObject['Datatype'] = 'TextureMappingPalette'
        
        RecordLength = self._readUShort()
        
        # Skip over the reserved area
        self._skip(4)
        
        newObject['TextureMappingIdx'] = self._readUInt()
        newObject['TextureMappingName'] = self._readString(20)
        newObject['TextureMappingType'] = self._readUInt()
        
        if newObject['TextureMappingType'] not in [0, 1, 2, 4, 5, 6]:
            raise Exception("Unable to determine texture mapping type.")
        
        newObject['WarpedFlag'] = self._readInt()
        
        newObject['TransformationMatrix'] = np.zeros((4, 4))
        for n in range(16):
            # Enter elements of a matrix by going across their columns
            newObject['TransformationMatrix'][int(n) / 4, n % 4] = self._readDouble()
        
        # Now branch depending on what texture map was recognised.
        if newObject['TextureMappingType'] == 1:
            # Parameters for 3 point put texture mapping
            newObject['PutTextureToolState'] = self._readInt()
            if newObject['PutTextureToolState'] not in [0, 1, 2, 3]:
                raise Exception("Unable to determine put texture tool state.")
            
            newObject['ActiveGeometryPoint'] = self._readInt()            
            if newObject['ActiveGeometryPoint'] not in [1, 2, 3]:
                raise Exception("Unable to determine active geometry point.")
            
            varNames = ['LowerLeftCorner', 'UpperRightCorner']
            for varName in varNames:
                newObject[varName] = np.zeros((1, 3))
                for colIdx in range(3):
                    newObject[varName][0, colIdx] = self._readDouble()
            
            newObject['UseRealWorldSizeFlags'] = []
            for idx in range(3):
                newObject['UseRealWorldSizeFlags'].append(self._readInt())
            
            # Skip over reserved area
            self._skip(4)
            
            pointTypes = ['Texture', 'Geometry']
            varNames = ['Origin', 'Alignment', 'Shear']
            for pointType in pointTypes:
                for varName in varNames:
                    newObject[pointType + varName] = np.zeros((1, 3))
                    for colIdx in range(3):
                        newObject[pointType + varName][0, colIdx] = self._readDouble()
            
            newObject['ActiveTexturePoint'] = self._readInt()            
            if newObject['ActiveTexturePoint'] not in [1, 2, 3]:
                raise Exception("Unable to determine active texture point.")
            
            newObject['UVDisplayType'] = self._readInt()            
            if newObject['UVDisplayType'] not in [1, 2]:
                raise Exception("Unable to determine UV display type.")
            
            varTypes = ['URepetition', 'VRepetition']
            for varType in varTypes:
                newObject[varType] = self._readFloat()
        elif newObject['TextureMappingType'] == 2:
            # Parameters for 4 point put texture mapping
            newObject['PutTextureToolState'] = self._readInt()
            if newObject['PutTextureToolState'] not in [0, 1, 2, 3, 4]:
                raise Exception("Unable to determine put texture tool state.")
            
            newObject['ActiveGeometryPoint'] = self._readInt()            
            if newObject['ActiveGeometryPoint'] not in [1, 2, 3, 4]:
                raise Exception("Unable to determine active geometry point.")
            
            varNames = ['LowerLeftCorner', 'UpperRightCorner']
            for varName in varNames:
                newObject[varName] = np.zeros((1, 3))
                for colIdx in range(3):
                    newObject[varName][0, colIdx] = self._readDouble()
            
            newObject['UseRealWorldSizeFlags'] = []
            for idx in range(3):
                newObject['UseRealWorldSizeFlags'].append(self._readInt())
            
            # Skip over reserved area
            self._skip(4)
            
            pointTypes = ['Texture', 'Geometry']
            varNames = ['Origin', 'Alignment', 'Shear', 'Perspective']
            for pointType in pointTypes:
                for varName in varNames:
                    newObject[pointType + varName] = np.zeros((1, 3))
                    for colIdx in range(3):
                        newObject[pointType + varName][0, colIdx] = self._readDouble()
            
            newObject['ActiveTexturePoint'] = self._readInt()            
            if newObject['ActiveTexturePoint'] not in [1, 2, 3, 4]:
                raise Exception("Unable to determine active texture point.")
            
            newObject['UVDisplayType'] = self._readInt()            
            if newObject['UVDisplayType'] not in [1, 2]:
                raise Exception("Unable to determine UV display type.")
            
            newObject['DepthScaleFactor'] = self._readFloat()
            
            self._skip(4)
            
            newObject['FourPointTransformationMatrix'] = np.zeros((4, 4))
            for n in range(16):
                # Enter elements of a matrix by going across their columns
                newObject['FourPointTransformationMatrix'][int(n) / 4, n % 4] = self._readDouble()
            
            varTypes = ['URepetition', 'VRepetition']
            for varType in varTypes:
                newObject[varType] = self._readFloat()
        elif newObject['TextureMappingType'] == 4:
            # Parameters for spherical project texture mapping
            newObject['Scale'] = self._readFloat()
            
            self._skip(4)
            
            newObject['Centre'] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject['Centre'][0, colIdx] = self._readDouble()
            
            varNames = ['ScaleBoundingBox', 'MaxDimensionMappedGeometryBoundingBox']
            for varName in varNames:
                newObject[varName] = self._readFloat()
        elif newObject['TextureMappingType'] == 5:
            # Parameters for radial project texture mapping
            newObject['ActiveGeometryPoint'] = self._readUInt()
            if newObject['ActiveGeometryPoint'] not in [1, 2]:
                raise Exception('Unable to determine active geometry point.')
            
            self._skip(4)
            
            varNames = ['RadialScale', 'CylinderLengthScale']
            for varType in varTypes:
                newObject[varType] = self._readFloat()
            
            newObject['XYTransformationMatrix'] = np.zeros((4, 4))
            for n in range(16):
                # Enter elements of a matrix by going across their columns
                newObject['XYTransformationMatrix'][int(n) / 4, n % 4] = self._readDouble()
            
            varNames = ['EndPoint1', 'EndPoint2']
            for varName in varNames:
                newObject[varName] = np.zeros((1, 3))
                for colIdx in range(3):
                    newObject[varName][0, colIdx] = self._readDouble()
        else:
            print("Unable to handle to type of texture mapping type. Skipping this section.")
        
        # Now check to see if the warped mapping was enabled
        if newObject['WarpedFlag'] == 1:
            varNames = ['WarpedActiveGeometryPoint', 'WarpToolState']
            for varName in varNames:
                newObject[varName] = self._readUInt()
            
            # Skip over reserved area
            self._skip(8)
            
            varNames = ['WarpedFrom', 'WarpedTo']
            for varName in varNames:
                newObject[varName] = np.zeros((8, 2))
                for rowIdx in range(8):
                    for colIdx in range(2):
                        newObject[varName][rowIdx, colIdx] = self._readDouble()
        
        # Finally, save this variable to the stack
        self._addObject(newObject)
    
    def _opMatPalette(self):
        # Opcode 113
        newObject = dict()
        newObject['Datatype'] = "MaterialPalette"
        newObject['MaterialIndex'] = self._readUInt()
        newObject['MaterialName'] = self._readString(12)
        newObject['Flags'] = self._readUInt()
        
        componentTypes = ['Ambient', 'Diffuse', 'Specular', 'Emissive']
        for component in componentTypes:
            newObject[component] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[component][0, colIdx] = self._readFloat()
        
        newObject['Shininess'] = self._readFloat()
        newObject['Alpha'] = self._readFloat()
        
        # Now skip over a reserved spot
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opNameTable(self):
        # Opcode 114
        newObject = dict()
        # Read the data to memeory and extract data as normal with modified
        # read functions
        self._readChunk()
        
        newObject['NumberOfNames'] = self._readInt(fromChunk = True)
        newObject['NextAvailableNameIndex'] = self._readUShort(fromChunk = True)
        
        newObject['NameIndex'] = []
        newObject['NameString'] = []
        
        for nameIndex in range(newObject['NumberOfNames']):
            entryLength = self._readInt(fromChunk = True)
            if entryLength > 86:
                raise Exception('Name table entry ' + str(nameIndex) + ' exceeds the maximum allowable size.')
            newObject['NameIndex'].append(self._readUInt(fromChunk = True))
            newObject['NameString'].append(self._readString(entryLength - 6, fromChunk = True))
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opCAT(self):
        # Opcode 115
        newObject = dict()
        newObject['Datatype'] = "CAT"
        RecordLength = self._readUShort()
        self._skip(4)
        newObject['IRColourCode'] = self._readInt()
        newObject['DrawType'] = self._readInt()
        if newObject['DrawType'] not in [0, 1, 2]:
            raise Exception('Unable to determine draw type.')
        newObject['TextureWhite'] = self._readBool()
        self._skip(2)
        newObject['ColourNameIdx'] = self._readUShort()
        newObject['AltColourNameIdx'] = self._readUShort()
        
        varNames = ['DetailTexturePatternIdx', 'TexturePatternIdx', 'MaterialIdx']
        
        for varName in varNames:
            newObject[varName] = self._readShort()
            if newObject[varName] == -1:
                newObject[varName] = None
        
        newObject['SurfaceMaterialCode'] = self._readShort()
        newObject['IRMaterialCode'] = self._readUInt()
        self._skip(8)
        newObject['TextureMappingIdx'] = self._readShort()
        self._skip(2)
        newObject['PrimaryColourIdx'] = self._readUInt()
        newObject['AltColourIdx'] = self._readUInt()
        self._skip(12)
        newObject['Flags'] = self._readUInt()
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opCATData(self):
        # Opcode 116
        newObject = dict()
        newObject['Datatype'] = 'CATData'
        
        RecordLength = self._readUShort()
        
        subtype = self._readInt()
        
        if subtype == 1:
            newObject['Subtype'] = 'CATDataHeader'
            varNames = ['MaxNumber', 'ActualNumber', 'TotalLengthOfPackedFaceData']
            for varName in varNames:
                newObject[varName] = self._readInt()
            self._skip(12)
            
            newObject['FaceIndex'] = []
            newObject['FaceDataOffset'] = []
            
            for faceIdx in range(newObject['ActualNumber']):
                newObject['FaceIndex'].append(self._readInt())
                self._skip(4)
                newObject['FaceDataOffset'].append(self._readInt())
        elif subtype == 2:
            newObject['Subtype'] = 'CATDataFace'
            newObject['TotalLengthOfPackedFaceRecords'] = self._readInt()
            
            newObject['FaceRecords'] = []
            
            for faceIdx in range(newObject['TotalLengthOfPackedFaceRecords']):
                faceRecord = dict()
                
                varNames = ['LevelOfDetail', 'ChildIndex1', 'ChildIndex2', 'ChildIndex3', 'ChildIndex4', 'IDLength']
                
                for varName in varNames:
                    faceRecord[varName] = self._readInt()
                
                faceRecord['ID'] = self._readString(faceRecord['IDLength'])
                
                newObject['FaceRecords'].append(faceRecord)
        else:
            raise Exception('Unable to determine subtype.')
        
        self._addObject(newObject)
    
    
    def _opBoundHist(self):
        # Opcode 119
        RecordLength = self._readUShort()
        
        # And as the contents of the record is "reserved for use by Multigen-Paradigm",
        # then skip to the end of the record
        self._skip(RecordLength - 4)
    
    
    def _opPushAttr(self):
        # Opcode 122
        pass
    
    
    def _opPopAttr(self):
        # Opcode 123
        pass
    
    
    def _opCurve(self):
        # Opcode 126
        newObject = dict()
        newObject['Datatype'] = 'Curve'
        
        RecordLength = self._readUShort()
        
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['CurveType'] = self._readUInt()
        if newObject['CurveType'] not in [4, 5, 6]:
            raise Exception("Unable to determine curve type.")
        
        newObject['NumberOfControlPoints'] = self._readUInt()
        
        self._skip(4)
        
        newObject['Coordinates'] = np.zeros((newObject['NumberOfControlPoints'], 3))
        for rowIdx in range(newObject['NumberOfControlPoints']):
            for colIdx in range(3):
                newObject['Coordinates'][rowIdx, colIdx] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opRoadConstruc(self):
        # Opcode 127
        newObject = dict()
        newObject['Datatype'] = 'RoadConstruction'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        varNames = ['RoadType', 'RoadToolsVersion']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        if newObject['RoadType'] not in [0, 1, 2]:
            raise Exception("Unable to determine road type.")
        
        varNames = ['EntryPoint', 'AlignmentPoint', 'ExitPoint']
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        varNames = ['ArcRadius', 'EntrySpiralLength', 'ExitSpiralLength', 'Superelevation']
        for varName in varNames:
            newObject[varName] = self._readDouble()
        
        newObject['SpiralType'] = self._readUInt()
        if newObject['SpiralType'] not in [0, 1, 2]:
            raise Exception("Unable to determine spiral type.")
        
        newObject['VerticalParabolaFlag'] = self._readUInt()
        
        varNames = ['VerticalCurveLength', 'MinimumCurveLength', 'EntrySlope', 'ExitSlope']
        for varName in varNames:
            newObject[varName] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opLightPtAppearPalette(self):
        # Opcode 128
        newObject = dict()
        newObject['Datatype'] = 'LightPointAppearancePalette'
        
        # Skip over reserved area
        self._skip(4)
        
        newObject['AppearanceName'] = self._readString(256)
        newObject['AppearanceIndex'] = self._readUInt()
        
        newObject['SurfaceMaterialCode'] = self._readUShort()
        newObject['FeatureID'] = self._readUShort()
        newObject['BackColourBiDir'] = self._readUInt()
        
        newObject['DisplayMode'] = struct.unpack('>H', self.f.read(4))[0]
        if newObject['DisplayMode'] not in [0, 1, 2]:
            raise Exception("Unable to determine display mode.")
        
        varNames = ['Intensity', 'BackIntensity', 'MinimumDefocus', 'MaximumDefocus']
        for varName in varNames:
            newObject[varNames] = self._readFloat()
        
        varNames = ['FadingMode', 'FogPunchMode', 'DirectionalMode', 'RangeMode']
        for varName in varNames:
            newObject[varNames] = self._readUInt()
        
        varNames = ['MinPixelSize', 'MaxPixelSize', 'ActualSize', 'TransparentFalloffPixelSize', 'TransparentFalloffExponent', 'TransparentFalloffScalar', 'TransparentFalloffClamp', 'FogScalar', 'SizeDifferenceThreshold']
        for varName in varNames:
            newObject[varNames] = self._readFloat()
        
        newObject['Directionality'] = self._readUInt()
        if newObject['Directionality'] not in [0, 1, 2]:
            raise Exception("Unable to determine directionality.")
        
        varNames = ['HorizontalLobeAngle', 'VerticalLobeAngle', 'DirectionalFalloffExponent', 'DirectionalAmbientIntensity', 'Significance']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        newObject['Flags'] = self._readUInt()
        
        varNames = ['VisibilityRange', 'FadeRangeRatio', 'FadeInDuration', 'FadeOutDuration', 'LODRangeRatio', 'LODScale']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        newObject['TexturePatternIdx'] = self._readShort()
        
        # Skip over reserved area
        self._skip(2)
        
        self._addObject(newObject)
    
    
    def _opLightPtAnimatPalette(self):
        # Opcode 129
        newObject = dict()
        newObject['Datatype'] = 'LightPointAnimationPalette'
        
        RecordLength = self._readUShort()
        
        # Skip over the reserved area
        self._skip(4)
        
        newObject['AnimationName'] = self._readString(256)
        newObject['AnimationIndex'] = self._readUInt()
        
        varNames = ['AnimationPeriod', 'AnimationPhaseDelay', 'AnimationEnabledPeriod']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        newObject['AxisOfRotation'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['AxisOfRotation'][0, colIdx] = self._readFloat()
        
        varNames = ['Flags', 'AnimationType', 'MorseCodeTiming', 'WordRate', 'CharacterRate']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        newObject['MorseCodeString'] = self._readString(1024)
        newObject['NumberOfSequences'] = self._readUInt()
        
        varNames = ['SequenceState', 'SequenceDuration', 'SequenceColour']
        dataTypes = [self._readUInt, self._readFloat, self._readUInt]
        
        for varName in varNames:
            newObject[varName] = []
        
        for idx in range(newObject['NumberOfSequences']):
            for varName, dataType in zip(varNames, dataTypes):
                newObject[varName].append(dataType())
        
        self._addObject(newObject)
    
    
    def _opIdxLightPt(self):
        # Opcode 130
        newObject = dict()
        newObject['Datatype'] = 'IndexedLightPoint'
        
        newObject['ASCIIID'] = self._readString(8)
        
        varNames = ['AppearanceIndex', 'AnimationIndex', 'DrawOrder']
        for varName in varNames:
            newObject[varName] = self._readInt()
        
        # Skip over reserved area:
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opLightPtSys(self):
        # Opcode 131
        newObject = dict()
        newObject['Datatype'] = 'LightPointSystem'
        newObject['ASCIIID'] = self._readString(8)
        newObject['Intensity'] = self._readFloat()
        
        newObject['AnimationState'] = self._readUInt()
        if newObject['AnimationState'] not in [0, 1, 2]:
            raise Exception('Unable to determine animation state.')
        
        newObject['Flags'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opIdxStr(self):
        # Opcode 132
        newObject = dict()
        
        RecordLength = self._readUShort()
        newObject['Datatype'] = 'IndexedString'
        newObject['Index'] = self._readUInt()
        newObject['ASCIIString'] = self._readString(RecordLength - 8)
        
        self._addObject(newObject)
    
    
    def _opShaderPalette(self):
        # Opcode 133
        newObject = dict()
        newObject['Datatype'] = 'ShaderPalette'
        
        RecordLength = self._readUShort()
        newObject['ShaderIdx'] = self._readUInt()
        newObject['ShaderType'] = self._readUInt()
        if newObject['ShaderType'] not in [0, 1, 2]:
            raise Exception("Unable to determine shader type.")
        
        newObject['ShaderName'] = self._readString(1024)
        
        # Now branch based on the shader type
        if newObject['ShaderType'] == 0:
            # Cg shader type
            varNames = ['VertexProgramFilename', 'FragmentProgramFilename']
            for varName in varNames:
                newObject[varName] = self._readString(1024)
            
            newObject['VertexProgramProfile'] = self._readInt()
            newObject['FragmentProgramProfile'] = self._readInt()
            
            varNames = ['VertexProgramEntryPoint', 'FragmentProgramEntryPoint']
            for varName in varNames:
                newObject[varName] = self._readString(256)
        elif newObject['ShaderType'] == 1:
            print("CgFX shader type has not been implemented. Skipping...")
            self._skip(RecordLength - 1036)
        else:
            # Only OpenGL shading language left (i.e. type 2)
            varNames = ['NumberOfVertexProgramFiles', 'NumberOfFragmentProgramFiles']
            for varName in varNames:
                newObject[varName] = self._readUInt()
            
            destVars = ['VertexProgramFiles', 'FragmentProgramFiles']
            
            # Note that the documentation states that these should be from 0 to the number of points
            # I'm assuming this is not inclusive (i.e. 0 to N - 1)
            for varName, destName in zip(varNames, destVars):
                newObject[destName] = []
                for idx in range(newObject[varName]):
                    newObject[destName].append(self._readString(1024))
        
        self._addObject(newObject)
    
    
    def _opExtMatHdr(self):
        # Opcode 135
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialHeader'
        
        newObject['MaterialIndex'] = self._readUInt()
        newObject['MaterialName'] = self._readString(12)
        newObject['Flags'] = self._readUInt()
        
        newObject['ShadeModel'] = self._readUInt()
        if newObject['ShadeModel'] not in [0, 1, 2]:
            raise Exception("Unable to determine shade model.")
            
        self._addObject(newObject)
    
    
    def _opExtMatAmb(self):
        # Opcode 136
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialAmbient'
        
        newObject['AmbientColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['AmbientColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatDif(self):
        # Opcode 137
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialDiffuse'
        
        newObject['DiffuseColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['DiffuseColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatSpc(self):
        # Opcode 138
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialSpecular'
        
        newObject['Shininess'] = self._readFloat()
        
        newObject['SpecularColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['SpecularColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatEms(self):
        # Opcode 139
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialEmissive'
        
        newObject['EmissiveColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['EmissiveColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatAlp(self):
        # Opcode 140
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialAlpha'
        
        newObject['Alpha'] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        newObject['Quality'] = self._readUInt()
        if newObject['Quality'] not in [0, 1]:
            raise Exception("Unable to determine quality.")
        
        self._addObject(newObject)
    
    
    def _opExtMatLightMap(self):
        # Opcode 141
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialLightMap'
        
        newObject['MaximumIntensity'] = self._readFloat()
        
        varNames = ['TextureIndex', 'UVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatNormMap(self):
        # Opcode 142
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialNormalMap'
        
        varNames = ['TextureIndex', 'UVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatBumpMap(self):
        # Opcode 143
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialBumpMap'
        
        varNames = ['TextureIndex', 'UVSet', 'TangentUVSet', 'BinormalUVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatShadowMap(self):
        # Opcode 145
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialShadowMap'
        
        newObject['MaximumIntensity'] = self._readFloat()
        
        varNames = ['TextureIndex', 'UVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatReflMap(self):
        # Opcode 147
        newObject = dict()
        newObject['Datatype'] = 'ExtendedMaterialReflectionMap'
        
        newObject['TintColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['TintColour'][0, colIdx] = self._readFloat()
        
        varNames = ['ReflectionTextureIndex', 'ReflectionUVSet', 'EnvironmentTextureIndex']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        # Skip over reserved area
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opExtGUIDPalette(self):
        # Opcode 148
        newObject = dict()
        newObject['Datatype'] = 'ExtensionGUIDPalette'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        
        # Documentation says that this is a 40 byte integer. I imply it's an integer (4 bytes) * 10.
        newObject['GUIDString'] = []
        for idx in range(10):
            newObject['GUIDString'].append(self._readUInt())
        
        self._addObject(newObject)
    
    
    def _opExtFieldBool(self):
        # Opcode 149
        newObject = dict()
        newObject['Datatype'] = 'ExtensionFieldBoolean'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldBoolean'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtFieldInt(self):
        # Opcode 150
        newObject = dict()
        newObject['Datatype'] = 'ExtensionFieldInteger'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldInteger'] = self._readInt()
        
        self._addObject(newObject)
    
    
    def _opExtFieldFloat(self):
        # Opcode 151
        newObject = dict()
        newObject['Datatype'] = 'ExtensionFieldFloat'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldFloat'] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opExtFieldDouble(self):
        # Opcode 152
        newObject = dict()
        newObject['Datatype'] = 'ExtensionFieldDouble'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldDouble'] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opExtFieldString(self):
        # Opcode 153
        newObject = dict()
        
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        newObject['Datatype'] = 'ExtensionFieldString'
        newObject['GUIDPaletteIdx'] = self._readUInt(fromChunk = True)
        newObject['StringLength'] = self._readUInt(fromChunk = True)
        newObject['ExtensionFieldString'] = self._readString(newObject['StringLength'], fromChunk = True)
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        
        self._addObject(newObject)
    
    
    def _opExtFieldXMLString(self):
        # Opcode 154
        newObject = dict()
        
        # Read the data to memory and extract data as normal with modified
        # read functions
        self._readChunk()
        
        newObject['Datatype'] = 'ExtensionFieldXMLString'
        newObject['GUIDPaletteIdx'] = self._readUInt(fromChunk = True)
        newObject['StringLength'] = self._readUInt(fromChunk = True)
        newObject['ExtensionFieldXMLString'] = self._readString(newObject['StringLength'], fromChunk = True)
        
        # The data chunk should be processed. Reset the variable to None:
        self._Chunk = None
        self._addObject(newObject)
    
    
    def _readChunk(self):
        """
            This function reads a block + a continuous block.
            This is an internal function.
        """
        
        # The very first element ought to be a record length for the primary header
        # block and this should be followed by the continous blocks.
        RecordLength = self._readUShort()
        
        # Then read everything except the header.
        chunk = self.f.read(RecordLength - 4)
        
        # Now determine if the next block is a continuous opcode
        opCode = self._readUShort()
        
        while opCode == 23:
            # See how much data needs to be extracted
            RecordLength = self._readUShort()
            
            # Append this record to the previous
            chunk += self.f.read(RecordLength - 4)
            
            # Now read the next opCode
            opCode = self._readUShort()
        # Previous instruction was to read the next opCode. If here, opCode was not a
        # continuous record, so back two bytes.
        self._skip(-2)
        # Save the chunk to a global variable
        self._Chunk = chunk
    
    
    def _cleanExternalFilename(self, fileName = None, isTexture = True):
        if fileName is None:
            if isTexture:
                raise IOError('No texture attribute filename specified.')
            else:
                raise IOError('No external reference filename specified.')
        
        if fileName[0] == '.':
            # This is based on a relative path. Extract the contents of the stored filename:
            if self.fileName is None:
                if isTexture:
                    raise IOError('Attribute file uses relative path names. Unable to determine relative path.')
                else:
                    raise IOError('External reference filename uses relative path names. Unable to determine relative path.')
            # If here, we can extract the path:
            fileName = os.path.dirname(self.fileName) + os.sep + fileName
        
        # Check to see if this can be accessed firstly.
        if not os.path.exists(fileName):
            # This file cannot be accessed as it is. Try replacing path separators as 
            # this filename is likely going to have different file separators.
            if '\\\\' in fileName:
                # Check to see if replacing these fixes the problem:
                if path.exists(fileName.replace('\\\\'), os.sep):
                    # Yes it does:
                    return fileName.replace('\\\\', os.sep)
                
            fileName = fileName.replace('\\\\', os.sep)
            fileName = fileName.replace('//', os.sep)
            fileName = fileName.replace('/', os.sep)
            
            if fileName.count('.') == 1:
                # It's possible that this hasn't been given a relative path. Check to see if this
                # '.' denotes an extension only.
                if fileName[-5:].count('.') == 1 and os.path.exists(os.path.dirname(self.fileName) + os.sep + fileName):
                    fileName = os.path.dirname(self.fileName) + os.sep + fileName
                else:
                    print '\t' * self._tabbing + 'Problems with filename: ' + fileName
                    # If here, the issue couldn't be resolved. Throw an error.
                    if isTexture:
                        raise IOError('Unable to translate texture filename with full path.')
                    else:
                        raise IOError('Unable to translate external reference filename with full path.')
            
            # Lastly, check to see if the escape character should be a file separator
            if '\\' in fileName and not os.path.exists(fileName):
                # Now check to see if converting these makes readable
                if os.path.exists(fileName.replace('\\', os.sep)):
                    fileName = fileName.replace('\\', os.sep)
                else:
                    print '\t' * self._tabbing + 'Problems with filename: ' + fileName
                    # If here, the issue couldn't be resolved. Throw an error.
                    if isTexture:
                        raise IOError('Unable to translate texture filename.')
                    else:
                        raise IOError('Unable to translate external reference filename.')
        
        # If here, assume that everything's (now) okay
        return fileName
    
    
    def _checkTextureFile(self, fileName = None):
        
        fileName = self._cleanExternalFilename(fileName)
        
        if fileName is None:
            raise IOError('No texture filename specified.')
        
        if not os.path.exists(fileName):
            if self._SkipMissingTextures:
                return None
            raise IOError('Could not find texture file.')
        
        # Determine if an attr file exists:
        attrFile = fileName + '.attr'
        if not os.path.exists(attrFile):
            # Now try to remove the previous extension and add attr extension
            if os.path.exists(fileName[:-3] + "attr"):
                attrFile = fileName[:-3] + "attr"
            else:
                raise IOError('Could not find texture attribute file.')
        
        return attrFile
    
    
    def _parseTextureFile(self, fileName = None):
        # Firstly, determine if the file exists
        if fileName is None:
            raise IOError('No texture filename specified.')
        
        # Now return a filename that we know should work
        fileName = self._checkTextureFile(fileName)
        
        if fileName is None:
            # Skip reading. Return an object that states this file could not be found.
            return "File could not be found."
        
        f = open(fileName, 'rb')
        
        # For parsing the texture file, we cannot use the shortcut commands created. Instead, define them within this function
        def readInt():
            return struct.unpack('>i', f.read(4))[0]
        
        def readFloat():
            return struct.unpack('>f', f.read(4))[0]
        
        def readDouble():
            return struct.unpack('>d', f.read(8))[0]
        
        def readString(noBytes):
            return struct.unpack('>' + str(noBytes) + 's', f.read(noBytes))[0].replace('\x00', '')
        
        def skip(noBytes):
            f.seek(noBytes, os.SEEK_CUR)
        
        try:
            f.seek(0)
            newObject = dict()
            newObject['Datatype'] = 'TextureAttribute'
            
            varNames = ['NumberOfTexelsU', 'NumberOfTexelsV', None, None, 'xUp', 'yUp', 'FileFormatType', 'MinificationFilterType', 'MagnificationFilterType', 'WrapMethod', 'WrapMethodUV', 'WrapMethodU', 'WrapMethodV', 'ModifiedFlag', 'xPivot', 'yPivot', 'EnvironmentType', 'IntensityPattern']
            for varName in varNames:
                if varName is None:
                    skip(4)
                else:
                    newObject[varName] = readInt()
            
            # Now process these readings:
            if newObject['FileFormatType'] not in range(6):
                raise Exception('Unable to determine file format type.')
            
            typeNames = ['AT&T image 8 pattern', 'AT&T image 8 template', 'SGI intensity modulation', 'SGI intensity with alpha', 'SGI RGB', 'SGI RGB with alpha']
            newObject['FileFormatName'] = typeNames[newObject['FileFormatType']]
            
            if newObject['MinificationFilterType'] not in range(13):
                raise Exception('Unable to determine minification filter type.')
            
            if newObject['MagnificationFilterType'] not in range(11):
                raise Exception('Unable to determine magnification filter type.')
            
            if newObject['WrapMethodUV'] not in [0, 1, 4]:
                raise Exception('Unable to determine wrap method u,v.')
            if newObject['WrapMethodU'] not in [0, 1, 3, 4]:
                raise Exception('Unable to determine wrap method u.')
            if newObject['WrapMethodV'] not in [0, 1, 3, 4]:
                raise Exception('Unable to determine wrap method v.')
            
            if newObject['EnvironmentType'] not in range(5):
                raise Exception('Unable to determine environment type.')
            
            # Finished processing. Now skip over a reserved area:
            # This skip is based on version OpenFlight versions prior to 16.1. After this,
            # an additional 4 bytes was added to instructions.
            skip(32)
            # skip(36)
            
            newObject['RealWorldSizeDirectionU'] = readDouble()
            newObject['RealWorldSizeDirectionV'] = readDouble()
            
            varNames = ['CodeForOriginOfImportedTexture', 'KernelVersionNumber', 'InternalFormatType', 'ExternalFormatType', 'MIPMAP']
            
            for varName in varNames:
                newObject[varName] = readInt()
            
            # Now process these readings:
            if newObject['InternalFormatType'] not in range(10):
                raise Exception('Unable to determine internal format type.')
            if newObject['ExternalFormatType'] not in range(3):
                raise Exception('Unable to determine external format type.')
            
            newObject['SeparableSymmetricFilterKernel'] = np.zeros((1, 8))
            for colIdx in range(8):
                newObject['SeparableSymmetricFilterKernel'][0, colIdx] = readFloat()
            
            newObject['SendTXControlPoints'] = readInt()
            
            for idx in range(8):
                newObject['LOD' + str(idx)] = readFloat()
                newObject['Scale' + str(idx)] = readFloat()
            
            newObject['ControlClamp'] = readFloat()
            
            newObject['AlphaMagnificationFilterType'] = readInt()
            if newObject['AlphaMagnificationFilterType'] not in range(11):
                raise Exception('Unable to determine magnification filter type for alpha.')
            newObject['ColourMagnificationFilterType'] = readInt()
            if newObject['ColourMagnificationFilterType'] not in range(11):
                raise Exception('Unable to determine magnification filter type for colour.')
            
            # Skip over reserved area:
            skip(36)
            
            varNames = ['CentralMeridian', 'UpperLatitude', 'LowerLatitude']
            
            for varName in varNames:
                newObject['LambertConicProjection' + varName] = readDouble()
            
            # Skip over reserved region:
            skip(28)
            
            varNames = ['Using', 'J', 'K', 'M', 'N', 'Scramble']
            for varName in varNames:
                newObject[varName + 'TXDetail'] = readInt()
            
            newObject['UsingTXTile'] = readInt()
            
            varNames = ['LowerLeftU', 'LowerLeftV', 'UpperRightU', 'UpperRightV']
            for varName in varNames:
                newObject[varName + 'TXTile'] = readFloat()
            
            varNames = ['Projection', 'EarthModel', None, 'UTMZone', 'ImageOrigin', 'GeospecificPointsUnits']
            for varName in varNames:
                if varName is None:
                    skip(4)
                else:
                    newObject[varName] = readInt()
            
            # Now validate the input:
            if newObject['Projection'] not in [0, 3, 4, 7]:
                raise Exception('Unable to determine projection.')
            
            if newObject['EarthModel'] not in range(5):
                raise Exception('Unable to determine earth model.')
            
            if newObject['ImageOrigin'] not in [0, 1]:
                raise Exception('Unable to determine image origin.')
            
            if newObject['GeospecificPointsUnits'] not in range(3):
                raise Exception('Unable to determine geospecific points units.')
            
            skip(8)
            newObject['HemisphereForGeospecificPointsUnits'] = readInt()
            if newObject['HemisphereForGeospecificPointsUnits'] not in [0, 1]:
                raise Exception('Unable to determine hemisphere for geospecific points units.')
            
            skip(12)
            newObject['TextureForCubemap'] = readInt()
            
            skip(588)
            newObject['Comments'] = readString(512)
            
            # This skip is based on version OpenFlight versions prior to 16.1. After this,
            # an additional 4 bytes was added to instructions.
            skip(52)
            # skip(56)
            
            newObject['AttributeFileVersionNumber'] = readInt()
            newObject['NumberOfGeospecificControlPoints'] = readInt()
            
            # Now process geospecific control point subrecord if there are some included.
            if newObject['NumberOfGeospecificControlPoints'] > 0:
                # There are records to process.
                skip(4)
                varNames = ['TexelU', 'TexelV', 'EarthCoordinateX', 'EarthCoordinateY']
                for idx in range(newObject['NumberOfGeospecificControlPoints']):
                    for varName in varNames:
                        newObject[varName + str(idx)] = readDouble()
                
                varNames = ['Left', 'Bottom', 'Right', 'Top']
                newObject['NumberOfSubtextures'] = readInt()
                # Now iterate through the number of subtextures if there are any.
                for idx in range('NumberOfSubtextures'):
                    newObject['Name' + str(idx)] = readString(32)
                    for varName in varNames:
                        newObject[varName + str(idx)] = readInt()
        except struct.error, e:
            print "\n" '\t' * self._tabbing + "Warning: Error parsing texture attribute file. Likely ended unexpectedly."
            print '\t' * self._tabbing + '\t Error message: ' + str(e) + '\n'
            f.close()
        except BaseException, e:
            f.close()
            # Now raise the exception outside the attribute parser so that it's picked up by the
            # exterior try-except.
            raise e
        finally:
            f.close()
        
        return newObject
