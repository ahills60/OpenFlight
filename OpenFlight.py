import os, struct
import numpy as np

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
        self._RecordType = 'Tree'
        self._TreeStack = []
        self._InstanceStack = []
    
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
        
        iRead = struct.unpack('>B', self.f.read(1))[0]
        
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
        
        iRead = struct.unpack('>i', self.f.read(4))[0]
        
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
            self._LastPlace = self.f.tell()
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
    
    def ReadFile(self, fileName = None):
        # Number of checks to perform        
        if fileName is None:
            if self.fileName is None:
                raise IOError('No filename specified.')
            fileName = self.fileName
        
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
        
        print "Reading OpenFlight file..."
        
        try:
            while True:
                iRead = self.f.read(2)
                if iRead == '':
                    break
                # There's some data.
                iRead = struct.unpack('>h', iRead)[0]
                print "Opcode read:", str(iRead)
                if iRead in self._ObsoleteOpCodes:
                    raise Exception("Unable to continue. File uses obsolete codes.")
                if iRead not in self._OpCodes:
                    raise Exception("Unable to continue OpenFlight Opcode not recognised.")
                # If here, there's a code that can be run.
                # Determine whether we should check the size of the block
                if self._OpCodes[iRead][1] is not None:
                    # There's a size we should check matches
                    RecordLength = struct.unpack('>H', self.f.read(2))[0]
                    if RecordLength != self._OpCodes[iRead][1]:
                        raise Exception("Unexpected " + self._OpCodes[iRead][2] + " record length")
                self._OpCodes[iRead][0](fileName)
                
                # Lastly, save this Opcode:
                self._PreviousOpCode = iRead
        except BaseException, e:
            if iRead not in self._OpCodes:
                print("An error occurred when calling Opcode " + str(iRead) + ".")
            else:
                print("An error occurred when calling Opcode " + str(iRead) + " (" + self._OpCodes[iRead][2]  + ").")
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
    
    def _opReserved(self, fileName = None):
        pass
    
    def _opHeader(self, fileName = None):
        # Opcode 1
        raise Exception("Another header found in file.")
    
    def _opGroup(self, fileName = None):
        # Opcode 2
        newObject = dict()
        
        newObject['DataType'] = "Group"
        newObject['ASCIIID'] = struct.unpack('>8s', self.f.read(8))[0].replace('\x00', '')
        newObject['RelativePriority'] = struct.unpack('>h', self.f.read(2))[0]
        
        # Skip some reserved spot
        self.f.seek(2, os.SEEK_CUR)
        
        newObject['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['FXID1'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['FXID2'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['Significance'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['LayerCode'] = struct.unpack('>B', self.f.read(1))[0]
        
        self.f.seek(5, os.SEEK_CUR)
        newObject['LoopCount'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['LoopDuration'] = struct.unpack('>f', self.f.read(4))[0]
        newObject['LastFrameDuration'] = struct.unpack('>f', self.f.read(4))[0]
        
        # Finally inject object into tree
        self._addObject(newObject)
    
    def _opObject(self, fileName = None):
        # Opcode 4
        newObject = dict()
        newObject['DataType'] = "Object"
        newObject['ASCIIID'] = struct.unpack('>8s', self.f.read(8))[0].replace('\x00', '')
        newObject['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['RelativePriority'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['Transparency'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['FXID1'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['FXID2'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['Significance'] = struct.unpack('>h', self.f.read(2))[0]
        self.f.seek(2, os.SEEK_CUR)
        
        self._addObject(newObject)
    
    def _opFace(self, fileName = None):
        # Opcode 5
        newObject = dict()
        newObject['DataType'] = "Face"
        newObject['ASCIIID'] = struct.unpack('>8s', self.f.read(8))[0].replace('\x00', '')
        newObject['IRColCode'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['RelativePriority'] = struct.unpack('>h', self.f.read(2))[0]
        
        newObject['DrawType'] = struct.unpack('>B', self.f.read(1))[0]
        
        drawTypes = [0, 1, 2, 3, 4, 8, 9, 10]
        if newObject['DrawType'] not in drawTypes:
            raise Exception("Unable to determine draw type.")
        
        newObject['TextureWhite'] = struct.unpack('>?', self.f.read(1))[0]
        newObject['ColourNameIdx'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['AltColourNameIdx'] = struct.unpack('>H', self.f.read(2))[0]
        
        # Skip over reserved
        self.f.seek(1, os.SEEK_CUR)
        
        templateTypes = [0, 1, 2, 4]
        newObject['Template'] = struct.unpack('>B', self.f.read(1))[0]
        if newObject['Template'] not in templateTypes:
            raise Exception("Unable to determine template type.")
        
        varNames = ['DetailTexturePatternIdx', 'TexturePatternIdx', 'MaterialIdx']
        
        for varName in varNames:
            newObject[varName] = struct.unpack('>h', self.f.read(2))[0]
            if newObject[varName] == -1:
                newObject[varName] = None
        
        newObject['SurfaceMaterialCode'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['FeatureID'] = struct.unpack('>h', self.f.read(2))[0]
        
        newObject['IRMaterialCode'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['Transparency'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['LODGenerationControl'] = struct.unpack('>B', self.f.read(1))[0]
        newObject['LineStyleIdx'] = struct.unpack('>B', self.f.read(1))[0]
        
        newObject['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        
        lightModes = [0, 1, 2, 3]
        newObject['LightMode'] = struct.unpack('>B', self.f.read(1))[0]
        if newObject['LightMode'] not in lightModes:
            raise Exception("Unable to determine light mode.")
        
        # Skip over reserved
        self.f.seek(7, os.SEEK_CUR)
        
        newObject['PackedColour'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['AltPackedColour'] = struct.unpack('>I', self.f.read(4))[0]
        
        newObject['TextureMappingIdx'] = struct.unpack('>h', self.f.read(2))[0]
        if newObject['TextureMappingIdx'] == -1:
            newObject['TextureMappingIdx'] = None
        
        self.f.seek(2, os.SEEK_CUR)
        
        newObject['PrimaryColourIdx'] = struct.unpack('>I', self.f.read(4))[0]
        if newObject['PrimaryColourIdx'] == -1:
            newObject['PrimaryColourIdx'] = None
        
        newObject['AltColourIdx'] = struct.unpack('>I', self.f.read(4))[0]
        if newObject['AltColourIdx'] == -1:
            newObject['AltColourIdx'] = None
        
        self.f.seek(2, os.SEEK_CUR)
        
        newObject['ShaderIdx'] = struct.unpack('>h', self.f.read(2))[0]
        if newObject['ShaderIdx'] == -1:
            newObject['ShaderIdx'] = None
        
        self._addObject(newObject)
    
    
    def _opPush(self, fileName = None):
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
    
    def _opPop(self, fileName = None):
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
            pass
        else:
            raise Exception("Unable to determine stack type.")
    
    def _opDoF(self, fileName = None):
        # Opcode 14
        newObject = dict()
        newObject['DataType'] = 'DegreeOfFreedom'
        newObject['ASCIIID'] = struct.unpack('>8s', self.f.read(8))[0].replace('\x00', '')
        
        # Skip over a reserved area
        self.f.seek(4, os.SEEK_CUR)
        
        varNames = ['DoFOrigin', 'DoFPointx', 'DoFPointxy']
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = struct.unpack('>d', self.f.read(8))[0]
        
        varNames = ['z', 'y', 'x', 'pitch', 'roll', 'yaw', 'zScale', 'yScale', 'xScale']
        variants = ['Min', 'Max', 'Current', 'Increment']
        
        for varName in varNames:
            for variant in variants:
                newObject[varName + variant] = struct.unpack('>d', self.f.read(8))[0]
        
        # Flags
        newObject['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        
        self.f.seek(4, os.SEEK_CUR)
        
        self._addObject(newObject)
    
    def _opPushSubface(self, fileName = None):
        # Opcode 19
        pass
    
    def _opPopSubface(self, fileName = None):
        # Opcode 20
        pass
    
    def _opPushExtension(self, fileName = None):
        # Opcode 21
        pass
    
    
    def _opPopExtension(self, fileName = None):
        # Opcode 22
        pass
    
    
    def _opContinuation(self, fileName = None):
        # Opcode 23
        # This function will require special handling as a continuation record extends previous records.
        raise Exception("Unexpected continuation record. This should have been handled by the " + self._OpCodes[self._PreviousOpCode][2] + " function.")
    
    
    def _opComment(self, fileName = None):
        # Opcode 31
        RecordLength = struct.unpack('>H', self.f.read(2))[0]
        
        newObject = dict()
        newObject['DataType'] = 'Comment'
        
        newObject['Text'] = struct.unpack('>' + (RecordLength - 4) + 's', self.f.read(RecordLength - 4))[0].replace('\x00', '')
        
        while RecordLength == 0xFFFF:
            # Expect a continuation record
            iRead = struct.unpack('>H', self.f.read(2))[0]
            
            if iRead != 23:
                # This is not a continuation record. Reverse and save variable
                self.f.seek(-2, os.SEEK_CUR)
                break
            # This is a continuation record, so get the record length
            RecordLength = struct.unpack('>H', self.f.read(2))[0]
            
            # Now continue appending to variable
            newObject['Text'] += struct.unpack('>' + (RecordLength - 4) + 's', self.f.read(RecordLength - 4))[0].replace('\x00', '')
        self._addObject(newObject)
    
    
    def _opColourPalette(self, fileName = None):
        # Opcode 32
        
        # Read the record length
        RecordLength = struct.unpack('>H', self.f.read(2))[0]
        
        newObject = dict()
        newObject['DataType'] = 'ColourPalette'
        
        # Skip a reserved area
        self.f.seek(128, os.SEEK_CUR)
        
        newObject['BrightestRGB'] = np.zeros((1024, 1))
        for rowIdx in range(1024):
            newObject['BrightestRGB'][rowIdx, 0] = struct.unpack('>I', self.f.read(4))[0]
        
        if RecordLength > 4228:
            # Include colour names
            
            # Read the number of colour names:
            noNames = struct.unpack('>I', self.f.read(4))[0]
            
            newObject['ColourNames'] = dict()
            
            for colourIdx in range(noNames):
                nameLength = struct.unpack('>H', self.f.read(2))[0]
                self.f.seek(2, os.SEEK_CUR)
                colIdx = struct.unpack('>H', self.f.read(2))[0]
                self.f.seek(2, os.SEEK_CUR)
                newObject['ColourNames'][colIdx] = stuct.unpack('>' + (nameLength - 8) + 's', self.f.read(nameLength - 8)).replace('\x00', '')[0]
        
        self._addObject(newObject)
    
    
    def _opLongID(self, fileName = None):
        # Opcode 33
        newObject = dict()
        newObject['DataType'] = 'LongID'
        
        RecordLength = struct.unpack('>H', self.f.read(2))[0]
        
        newObject['ASCIIID'] = struct.unpack('>' + (RecordLength - 4) + 's', self.f.read(RecordLength - 4))[0].replace('\x00', '')
        self._addObject(newObject)
    
    
    def _opMatrix(self, fileName = None):
        # Opcode 49        
        newObject = np.zeros((4, 4))
        for n in range(16):
            # Enter elements of a matrix by going across their columns
            newObject[int(n) / 4, n % 4] = struct.unpack('>f', self.f.read(4))[0]
        
        # Inject
        self._addObject(newObject)
    
    def _opVector(self, fileName = None):
        # Opcode 50
        newObject = dict()
        newObject['DataType'] = 'Vector'
        
        Components = ['i', 'j', 'k']
        for component in Components:
            newObject[component] = stuct.unpack('>f', self.f.read(4))[0]
        
        self._addObject(newObject)
    
    
    def _opMultitexture(self, fileName = None):
        # Opcode 52
        RecordLength = struct.unpack('>H', self.f.read(2))[0]
        
        newObject = dict()
        newObject['DataType'] = 'Multitexture'
        
        newObject['Mask'] = struct.unpack('>I', self.f.read(4))[0]
        
        varNames = ['TextureIndex', 'Effect', 'TextureMappingIndex', 'TextureData']
        for varName in varNames:
            newObject[varName] = []
        
        for textIdx in range((RecordLength / 8) - 1):
            for varName in varNames:
                newObject[varName].append(struct.unpack('>H', self.f.read(2))[0])
        
        self._addObject(newObject)
    
    def _opUVList(self, fileName = None):
        # Opcode 53
        pass
    
    
    def _opBSP(self, fileName = None):
        # Opcode 55
        pass
    
    
    def _opReplicate(self, fileName = None):
        # Opcode 60
        newObject = dict()
        newObject['DataType'] = 'Replicate'
        
        newObject['NoReplications'] = struct.unpack('>H', self.f.read(2))[0]
        
        # Skip over reserved space
        self.f.seek(2, os.SEEK_CUR)
        
        self._addObject(newObject)
    
    
    def _opInstRef(self, fileName = None):
        # Opcode 61        
        # Read instance number
        instance = struct.unpack('>I', self.f.read(4))[0]
        
        if instance not in self.Records["Instances"]:
            raise Exception("Could not find an instance to reference")
        
        # Now add this object to the right place
        self._addObject(self.Records["Instances"][instance])
    
    
    def _opInstDef(self, fileName = None):
        # Opcode 62
        # Firstly, set the record type to instance definition
        self._RecordType = "Instances"
        
        # Read instance number
        instance = struct.unpack('>I', self.f.read(4))[0]
        
        if instance in self.Records["Instances"]:
            raise Exception("Instance definition number has already been declared.")
        
        # There are no problems. Create an instance and prepare to accept incoming data
        self.Records["Instances"][instance] = []
        self._InstanceStack.append(instance)
    
    def _opExtRef(self, fileName = None):
        # Opcode 63
        newObject = dict()
        newObject['Datatype'] = "ExternalReference"
        newObject['ASCIIPath'] = struct.unpack('>200s', self.f.read(200))[0].replace('\x00', '')
        
        self.f.seek(4, os.SEEK_CUR)
        newObject["Flags"] = struct.unpack('>I', self.f.read(4))[0]
        newObject["BoundingBox"] = struct.unpack(">H", self.f.read(2))[0]
        self.f.seek(2, os.SEEK_CUR)
        
        # Inject into tree
        self._addObject(newObject)
    
    def _opTexturePalette(self, fileName = None):
        # Opcode 64
        newObject = dict()
        newObject['Datatype'] = "TexturePalette"
        newObject['Filename'] = struct.unpack('>200s', self.f.read(200))[0].replace('\x00', '')
        newObject['TexturePatternIdx'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['LocationInTexturePalette'] = np.zeros((1, 2))
        newObject['LocationInTexturePalette'][0, 0] = struct.unpack('>I', self.f.read(4))[0]
        newObject['LocationInTexturePalette'][0, 1] = struct.unpack('>I', self.f.read(4))[0]
        
        self._addObject(newObject)
    
    
    def _opVertexPalette(self, fileName = None):
        # Opcode 67
        newObject = dict()
        newObject['Datatype'] = "VertexPalette"
        newObject['Length'] = struct.unpack('>I', self.f.read(4))[0]
        
        self._addObject(newObject)
    
    
    def _opVertexColour(self, fileName = None):
        # Opcode 68
        newObject = dict()
        newObject['Datatype'] = "VertexColour"
        newObject['ColourNameIdx'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Flags'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = struct.unpack('>d', self.f.read(8))[0]
        
        newObject['PackedColour'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['VertexColourIndex'] = struct.unpack('>I', self.f.read(4))[0]
        
        self._addObject(newObject)
    
    
    def _opVertexColNorm(self, fileName = None):
        # Opcode 69
        newObject = dict()
        newObject['Datatype'] = "VertexColourWithNormal"
        newObject['ColourNameIdx'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Flags'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = struct.unpack('>d', self.f.read(8))[0]
        newObject['Normal'] = np.zeros((1, 3))
        # For i, j and k
        for colIdx in range(3):
            newObject['Normal'][0, colIdx] = struct.unpack('>f', self.f.read(4))[0]
        
        newObject['PackedColour'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['VertexColourIndex'] = struct.unpack('>I', self.f.read(4))[0]
        
        self.f.seek(4, os.SEEK_CUR)
        
        self._addObject(newObject)
    
    
    def _opVertexColNormUV(self, fileName = None):
        # Opcode 70
        newObject = dict()
        newObject['Datatype'] = "VertexColourWithNormalUV"
        newObject['ColourNameIdx'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Flags'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = struct.unpack('>d', self.f.read(8))[0]
        newObject['Normal'] = np.zeros((1, 3))
        # For i, j and k
        for colIdx in range(3):
            newObject['Normal'][0, colIdx] = struct.unpack('>f', self.f.read(4))[0]
        
        newObject['TextureCoordinate'] = np.zeros((1, 2))
        newObject['TextureCoordinate'][0, 0] = struct.unpack('>f', self.f.read(4))[0]
        newObject['TextureCoordinate'][0, 1] = struct.unpack('>f', self.f.read(4))[0]
        
        newObject['PackedColour'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['VertexColourIndex'] = struct.unpack('>I', self.f.read(4))[0]
        
        self.f.seek(4, os.SEEK_CUR)
        
        self._addObject(newObject)
    
    
    def _opVertexColUV(self, fileName = None):
        # Opcode 71
        newObject = dict()
        newObject['Datatype'] = "VertexColourWithUV"
        newObject['ColourNameIdx'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Flags'] = struct.unpack('>H', self.f.read(2))[0]
        newObject['Coordinate'] = np.zeros((1, 3))
        # For x, y and z
        for colIdx in range(3):
            newObject['Coordinate'][0, colIdx] = struct.unpack('>d', self.f.read(8))[0]
        
        newObject['TextureCoordinate'] = np.zeros((1, 2))
        newObject['TextureCoordinate'][0, 0] = struct.unpack('>f', self.f.read(4))[0]
        newObject['TextureCoordinate'][0, 1] = struct.unpack('>f', self.f.read(4))[0]
        
        newObject['PackedColour'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['VertexColourIndex'] = struct.unpack('>I', self.f.read(4))[0]
        
        self._addObject(newObject)
    
    
    def _opVertexList(self, fileName = None):
        # Opcode 72
        newObject = dict()
        newObject['Datatype'] = "VertexList"
        RecordLength = struct.unpack('>H', self.f.read(2))[0]
        
        newObject['ByteOffset'] = []
        
        for verIdx in range((RecordLength / 4) - 1):
            newObject['ByteOffset'].append(struct.unpack('>I', self.f.read(4))[0])
        
        # The below record length: 16383 * 4 = 65532 (0xFFFC) as max 65535 is (0xFFFF)
        while RecordLength >= 0xfffc:
            # Expect a continuation record
            iRead = struct.unpack('>H', self.f.read(2))[0]
            
            if iRead != 23:
                # This is not a continuation record. Reverse and save variable
                self.f.seek(-2, os.SEEK_CUR)
                break
            # This is a continuation record, so get the record length
            RecordLength = struct.unpack('>H', self.f.read(2))[0]
            
            # Now continue appending to variable
            for verIdx in range((RecordLength / 4) - 1):
                newObject['ByteOffset'].append(struct.unpack('>I', self.f.read(4))[0])
        self._addObject(newObject)
    
    
    def _opLoD(self, fileName = None):
        # Opcode 73
        newObject = dict()
        newObject['DataType'] = 'LevelOfDetail'
        newObject['ASCIIID'] = struct.unpack('>8s', self.f.read(8))[0].replace('\x00', '')
        
        # Skip over the reserved area
        self.read.seek(4, os.SEEK_CUR)
        
        newObject['SwitchInDistance'] = struct.unpack('>d', self.f.read(8))[0]
        newObject['SwitchOutDistance'] = struct.unpack('>d', self.f.read(8))[0]
        
        newObject['FXID1'] = struct.unpack('>h', self.f.read(2))[0]
        newObject['FXID2'] = struct.unpack('>h', self.f.read(2))[0]
        
        newObject['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        
        varNames = ['x', 'y', 'z']
        
        for varName in varNames:
            newObject[varName + 'Centre'] = struct.unpack('>d', self.f.read(8))[0]
        newObject['TransitionRange'] = struct.unpack('>d', self.f.read(8))[0]
        newObject['SignificantSize'] = struct.unpack('>d', self.f.read(8))[0]
        
        self._addObject(newObject)
    
    
    def _opBoundingBox(self, fileName = None):
        # Opcode 74
        
        newObject = dict()
        newObject['DataType'] = 'BoundingBox'
        
        # Skip over the reserved area
        self.f.seek(4, os.SEEK_CUR)
        
        Positions = ['Lowest', 'Highest']
        Axes = ['x', 'y', 'z']
        
        for position in Positions:
            for axis in Axes:
                newObject[axis + position] = struct.unpack('>d', self.f.read(8))[0]
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opRotEdge(self, fileName = None):
        # Opcode 76
        pass
    
    
    def _opTranslate(self, fileName = None):
        # Opcode 78
        pass
    
    
    def _opScale(self, fileName = None):
        # Opcode 79
        pass
    
    
    def _opRotPoint(self, fileName = None):
        # Opcode 80
        pass
    
    
    def _opRotScPoint(self, fileName = None):
        # Opcode 81
        pass
    
    
    def _opPut(self, fileName = None):
        # Opcode 82
        pass
    
    
    def _opEyeTrackPalette(self, fileName = None):
        # Opcode 83
        pass
    
    
    def _opMesh(self, fileName = None):
        # Opcode 84
        pass
    
    
    def _opLocVertexPool(self, fileName = None):
        # Opcode 85
        pass
    
    
    def _opMeshPrim(self, fileName = None):
        # Opcode 86
        pass
    
    
    def _opRoadSeg(self, fileName = None):
        # Opcode 87
        pass
    
    
    def _opRoadZone(self, fileName = None):
        # Opcode 88
        pass
    
    
    def _opMorphVertex(self, fileName = None):
        # Opcode 89
        pass
    
    
    def _opLinkPalette(self, fileName = None):
        # Opcode 90
        pass
    
    
    def _opSound(self, fileName = None):
        # Opcode 91
        pass
    
    
    def _opRoadPath(self, fileName = None):
        # Opcode 92
        pass
    
    
    def _opSoundPalette(self, fileName = None):
        # Opcode 93
        pass
    
    
    def _opGenMatrix(self, fileName = None):
        # Opcode 94
        pass
    
    
    def _opText(self, fileName = None):
        # Opcode 95
        pass
    
    
    def _opSwitch(self, fileName = None):
        # Opcode 96
        pass
    
    
    def _opLineStylePalette(self, fileName = None):
        # Opcode 97
        pass
    
    
    def _opClipRegion(self, fileName = None):
        # Opcode 98
        pass
    
    
    def _opExtension(self, fileName = None):
        # Opcode 100
        pass
    
    
    def _opLightSrc(self, fileName = None):
        # Opcode 101
        pass
    
    
    def _opLightSrcPalette(self, fileName = None):
        # Opcode 102
        pass
    
    
    def _opBoundSphere(self, fileName = None):
        # Opcode 105
        newObject = dict()
        newObject['DataType'] = 'BoundingSphere'
        
        # Skip over the reserved area
        self.f.seek(4, os.SEEK_CUR)
        
        newObject['Radius'] = struct.unpack('>d', self.f.read(8))[0]
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundCylinder(self, fileName = None):
        # Opcode 106
        newObject = dict()
        newObject['DataType'] = 'BoundingCylinder'
        
        # Skip over the reserved area
        self.f.seek(4, os.SEEK_CUR)
        
        newObject['Radius'] = struct.unpack('>d', self.f.read(8))[0]
        newObject['Height'] = struct.unpack('>d', self.f.read(8))[0]
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundConvexHull(self, fileName = None):
        # Opcode 107
        pass
    
    
    def _opBoundVolCentre(self, fileName = None):
        # Opcode 108
        newObject = dict()
        newObject['DataType'] = 'BoundingVolumeCentre'
        
        # Skip over the reserved area
        self.f.seek(4, os.SEEK_CUR)
        
        Axes = ['x', 'y', 'z']
        
        for axis in Axes:
            newObject[axis] = struct.unpack('>d', self.f.read(8))[0]
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundVolOrientation(self, fileName = None):
        # Opcode 109
        newObject = dict()
        newObject['DataType'] = 'BoundingVolumeOrientation'
        
        # Skip over the reserved area
        self.f.seek(4, os.SEEK_CUR)
        
        Angles = ['Yaw', 'Pitch', 'Roll']
        
        for angle in Angles:
            newObject[angle] = struct.unpack('>d', self.f.read(8))[0]
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    def _opLightPt(self, fileName = None):
        # Opcode 111
        pass
    
    
    def _opTextureMapPalette(self, fileName = None):
        # Opcode 112
        pass
    
    
    def _opMatPalette(self, fileName = None):
        # Opcode 113
        newObject = dict()
        newObject['DataType'] = "MaterialPalette"
        newObject['MaterialIndex'] = struct.unpack('>I', self.f.read(4))[0]
        newObject['MaterialName'] = struct.unpack('>12s', self.f.read(12))[0].replace('\x00', '')
        newObject['Flags'] = struct.unpack('>I', self.f.read(4))[0]
        
        componentTypes = ['Ambient', 'Diffuse', 'Specular', 'Emissive']
        for component in componentTypes:
            newObject[component] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[component][0, colIdx] = struct.unpack('>f', self.f.read(4))[0]
        
        newObject['Shininess'] = struct.unpack('>f', self.f.read(4))[0]
        newObject['Alpha'] = struct.unpack('>f', self.f.read(4))[0]
        
        # Now skip over a reserved spot
        self.f.seek(4, os.SEEK_CUR)
        
        self._addObject(newObject)
    
    
    def _opNameTable(self, fileName = None):
        # Opcode 114
        pass
    
    
    def _opCAT(self, fileName = None):
        # Opcode 115
        pass
    
    
    def _opCATData(self, fileName = None):
        # Opcode 116
        pass
    
    
    def _opBoundHist(self, fileName = None):
        # Opcode 119
        RecordLength = struct.unpack('>H', self.f.read(2))[0]
        
        # And as the contents of the record is "reserved for use by Multigen-Paradigm",
        # then skip to the end of the record
        self.f.seek(RecordLength - 4, os.SEEK_CUR)
    
    
    def _opPushAttr(self, fileName = None):
        # Opcode 122
        pass
    
    
    def _opPopAttr(self, fileName = None):
        # Opcode 123
        pass
    
    
    def _opCurve(self, fileName = None):
        # Opcode 126
        pass
    
    
    def _opRoadConstruc(self, fileName = None):
        # Opcode 127
        pass
    
    
    def _opLightPtAppearPalette(self, fileName = None):
        # Opcode 128
        pass
    
    
    def _opLightPtAnimatPalette(self, fileName = None):
        # Opcode 129
        pass
    
    
    def _opIdxLightPt(self, fileName = None):
        # Opcode 130
        pass
    
    
    def _opLightPtSys(self, fileName = None):
        # Opcode 131
        pass
    
    
    def _opIdxStr(self, fileName = None):
        # Opcode 132
        pass
    
    
    def _opShaderPalette(self, fileName = None):
        # Opcode 133
        pass
    
    
    def _opExtMatHdr(self, fileName = None):
        # Opcode 135
        pass
    
    
    def _opExtMatAmb(self, fileName = None):
        # Opcode 136
        pass
    
    
    def _opExtMatDif(self, fileName = None):
        # Opcode 137
        pass
    
    
    def _opExtMatSpc(self, fileName = None):
        # Opcode 138
        pass
    
    
    def _opExtMatEms(self, fileName = None):
        # Opcode 139
        pass
    
    
    def _opExtMatAlp(self, fileName = None):
        # Opcode 140
        pass
    
    
    def _opExtMatLightMap(self, fileName = None):
        # Opcode 141
        pass
    
    
    def _opExtMatNormMap(self, fileName = None):
        # Opcode 142
        pass
    
    
    def _opExtMatBumpMap(self, fileName = None):
        # Opcode 143
        pass
    
    
    def _opExtMatShadowMap(self, fileName = None):
        # Opcode 145
        pass
    
    
    def _opExtMatReflMap(self, fileName = None):
        # Opcode 147
        pass
    
    
    def _opExtGUIDPalette(self, fileName = None):
        # Opcode 148
        pass
    
    
    def _opExtFieldBool(self, fileName = None):
        # Opcode 149
        pass
    
    
    def _opExtFieldInt(self, fileName = None):
        # Opcode 150
        pass
    
    
    def _opExtFieldFloat(self, fileName = None):
        # Opcode 151
        pass
    
    
    def _opExtFieldDouble(self, fileName = None):
        # Opcode 152
        pass
    
    
    def _opExtFieldString(self, fileName = None):
        # Opcode 153
        pass
    
    
    def _opExtFieldXMLString(self, fileName = None):
        # Opcode 154
        pass
    
