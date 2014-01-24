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
    
    def _readString(self, size):
        return struct.unpack('>' + str(size) + 's', self.f.read(size))[0].replace('\x00', '')
    
    def _readFloat(self):
        return struct.unpack('>f', self.f.read(4))[0]
    
    def _readDouble(self):
        return struct.unpack('>d', self.f.read(8))[0]
    
    def _readUShort(self):
        return struct.unpack('>H', self.f.read(2))[0]
    
    def _readShort(self):
        return struct.unpack('>h', self.f.read(2))[0]
    
    def _readUInt(self):
        return struct.unpack('>I', self.f.read(4))[0]
    
    def _readInt(self):
        return struct.unpack('>i', self.f.read(4))[0]
    
    def _readBool(self):
        return struct.unpack('>?', self.f.read(1))[0]
    
    def _readUChar(self):
        return struct.unpack('>B', self.f.read(1))[0]
    
    def _readSChar(self):
        return struct.unpack('>b', self.f.read(1))[0]
    
    def _readChar(self):
        return struct.unpack('>c', self.f.read(1))[0]
    
    def _skip(self, noBytes):
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
        
        print "Determining record type... ",
        iRead = self._readShort()
        
        recognised = [iRead == this for this in recognisableRecordTypes]
        
        if not any(recognised):
            raise Exception("Unidentifiable record type")
        
        print "\rDetermining record length... ",
        recordLength = self._readUShort()
        
        if recordLength != recognisableRecordSizes[recognised.index(True)]:
            raise Exception("Unexpected record length.")
        
        print "\rReading record name... ",
        
        self.DBName  = self._readString(8)
        
        print "\rRead database name \"" + self.DBName + "\"\n"
        
        print "Determining file format revision number... ",
        iRead = self._readInt()
        
        if iRead not in self._OpenFlightFormats:
            raise Exception("Unrecognised OpenFlight file format revision number.")
        print "\rDatabase is written in the " + self._OpenFlightFormats[iRead] + " file format.\n"
        
        # We're not interested in the edit revision number, so skip that:
        self._skip(4)
        
        print "Determining date and time of last revision... ",
        
        # Next up is the date and time of the last revision
        iRead = self._readString(32)
        
        print "\rRecorded date and time of last revision: " + iRead + "\n"
        
        print "Extracting Node ID numbers... ",
        
        self.PrimaryNodeID['Group'] = self._readUShort()
        self.PrimaryNodeID['LOD'] = self._readUShort()
        self.PrimaryNodeID['Object'] = self._readUShort()
        self.PrimaryNodeID['Face'] = self._readUShort()
        
        print "\rValidating unit multiplier... ",
        
        iRead = self._readUShort()
        
        if iRead != 1:
            raise Exception("Unexpected value for unit multiplier.")
        
        print "\rExtracting scene settings... ",
        
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
                    RecordLength = self._readUShort()
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
        newObject['LoopCount'] = self._readUInt()
        newObject['LoopDuration'] = self._readFloat()
        newObject['LastFrameDuration'] = self._readFloat()
        
        # Finally inject object into tree
        self._addObject(newObject)
    
    def _opObject(self, fileName = None):
        # Opcode 4
        newObject = dict()
        newObject['DataType'] = "Object"
        newObject['ASCIIID'] = self._readString(8)
        newObject['Flags'] = self._readUInt()
        newObject['RelativePriority'] = self._readShort()
        newObject['Transparency'] = self._readUShort()
        newObject['FXID1'] = self._readShort()
        newObject['FXID2'] = self._readShort()
        newObject['Significance'] = self._readShort()
        self._skip(2)
        
        self._addObject(newObject)
    
    def _opFace(self, fileName = None):
        # Opcode 5
        newObject = dict()
        newObject['DataType'] = "Face"
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
        RecordLength = self._readUShort()
        
        newObject = dict()
        newObject['DataType'] = 'Comment'
        
        newObject['Text'] = self._readString(RecordLength - 4)
        
        while RecordLength == 0xFFFF:
            # Expect a continuation record
            iRead = self._readUShort()
            
            if iRead != 23:
                # This is not a continuation record. Reverse and save variable
                self._skip(-2)
                break
            # This is a continuation record, so get the record length
            RecordLength = self._readUShort()
            
            # Now continue appending to variable
            newObject['Text'] += self._readString(RecordLength - 4)
        self._addObject(newObject)
    
    
    def _opColourPalette(self, fileName = None):
        # Opcode 32
        
        # Read the record length
        RecordLength = self._readUShort()
        
        newObject = dict()
        newObject['DataType'] = 'ColourPalette'
        
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
    
    
    def _opLongID(self, fileName = None):
        # Opcode 33
        newObject = dict()
        newObject['DataType'] = 'LongID'
        
        RecordLength = self._readUShort()
        
        newObject['ASCIIID'] = self._readString(RecordLength - 4)
        self._addObject(newObject)
    
    
    def _opMatrix(self, fileName = None):
        # Opcode 49        
        newObject = np.zeros((4, 4))
        for n in range(16):
            # Enter elements of a matrix by going across their columns
            newObject[int(n) / 4, n % 4] = = self._readFloat()
        
        # Inject
        self._addObject(newObject)
    
    def _opVector(self, fileName = None):
        # Opcode 50
        newObject = dict()
        newObject['DataType'] = 'Vector'
        
        Components = ['i', 'j', 'k']
        for component in Components:
            newObject[component] = = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opMultitexture(self, fileName = None):
        # Opcode 52
        RecordLength = self._readUShort()
        
        newObject = dict()
        newObject['DataType'] = 'Multitexture'
        
        newObject['Mask'] = self._readUInt()
        
        varNames = ['TextureIndex', 'Effect', 'TextureMappingIndex', 'TextureData']
        for varName in varNames:
            newObject[varName] = []
        
        for textIdx in range((RecordLength / 8) - 1):
            for varName in varNames:
                newObject[varName].append(self._readUShort())
        
        self._addObject(newObject)
    
    def _opUVList(self, fileName = None):
        # Opcode 53
        pass
    
    
    def _opBSP(self, fileName = None):
        # Opcode 55
        newObject = dict()
        newObject['DataType'] = 'BinarySeparatingPlane'
        newObject['ASCIIID'] = self._readString(8)
        
        self._skip(4)
        
        newObject['PlaneEquationCoeffs'] = np.zeros((1, 4))
        for colIdx in range(4):
            newObject['PlaneEquationCoeffs'][0, colIdx] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opReplicate(self, fileName = None):
        # Opcode 60
        newObject = dict()
        newObject['DataType'] = 'Replicate'
        
        newObject['NoReplications'] = self._readUShort()
        
        # Skip over reserved space
        self._skip(2)
        
        self._addObject(newObject)
    
    
    def _opInstRef(self, fileName = None):
        # Opcode 61        
        # Read instance number
        instance = self._readUInt()
        
        if instance not in self.Records["Instances"]:
            raise Exception("Could not find an instance to reference")
        
        # Now add this object to the right place
        self._addObject(self.Records["Instances"][instance])
    
    
    def _opInstDef(self, fileName = None):
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
    
    def _opExtRef(self, fileName = None):
        # Opcode 63
        newObject = dict()
        newObject['Datatype'] = "ExternalReference"
        newObject['ASCIIPath'] = self._readString(200)
        
        self._skip(4)
        newObject["Flags"] = self._readUInt()
        newObject["BoundingBox"] = self._readUShort()
        self._skip(2)
        
        # Inject into tree
        self._addObject(newObject)
    
    def _opTexturePalette(self, fileName = None):
        # Opcode 64
        newObject = dict()
        newObject['Datatype'] = "TexturePalette"
        newObject['Filename'] = self._readString(200)
        newObject['TexturePatternIdx'] = self._readUInt()
        newObject['LocationInTexturePalette'] = np.zeros((1, 2))
        for colIdx in range(2):
            newObject['LocationInTexturePalette'][0, colIdx] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opVertexPalette(self, fileName = None):
        # Opcode 67
        newObject = dict()
        newObject['Datatype'] = "VertexPalette"
        newObject['Length'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opVertexColour(self, fileName = None):
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
    
    
    def _opVertexColNorm(self, fileName = None):
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
            newObject['Normal'][0, colIdx] = = self._readFloat()
        
        newObject['PackedColour'] = self._readUInt()
        newObject['VertexColourIndex'] = self._readUInt()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opVertexColNormUV(self, fileName = None):
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
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opVertexColUV(self, fileName = None):
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
    
    
    def _opVertexList(self, fileName = None):
        # Opcode 72
        newObject = dict()
        newObject['Datatype'] = "VertexList"
        RecordLength = self._readUShort()
        
        newObject['ByteOffset'] = []
        
        for verIdx in range((RecordLength / 4) - 1):
            newObject['ByteOffset'].append(self._readUInt())
        
        # The below record length: 16383 * 4 = 65532 (0xFFFC) as max 65535 is (0xFFFF)
        while RecordLength >= 0xfffc:
            # Expect a continuation record
            iRead = self._readUShort()
            
            if iRead != 23:
                # This is not a continuation record. Reverse and save variable
                self._skip(-2)
                break
            # This is a continuation record, so get the record length
            RecordLength = self._readUShort()
            
            # Now continue appending to variable
            for verIdx in range((RecordLength / 4) - 1):
                newObject['ByteOffset'].append(self._readUInt())
        self._addObject(newObject)
    
    
    def _opLoD(self, fileName = None):
        # Opcode 73
        newObject = dict()
        newObject['DataType'] = 'LevelOfDetail'
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
    
    
    def _opBoundingBox(self, fileName = None):
        # Opcode 74
        
        newObject = dict()
        newObject['DataType'] = 'BoundingBox'
        
        # Skip over the reserved area
        self._skip(4)
        
        Positions = ['Lowest', 'Highest']
        Axes = ['x', 'y', 'z']
        
        for position in Positions:
            for axis in Axes:
                newObject[axis + position] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opRotEdge(self, fileName = None):
        # Opcode 76
        newObject = dict()
        newObject['DataType'] = 'RotateAboutEdge'
        
        self._skip(4)
        
        varNames = ['FirstPoint', 'SecondPoint']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        newObject['Angle'] = self._readFloat()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opTranslate(self, fileName = None):
        # Opcode 78
        newObject = dict()
        newObject['DataType'] = 'Translate'
        
        self._skip(4)
        
        varNames = ['From', 'Delta']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opScale(self, fileName = None):
        # Opcode 79
        newObject = dict()
        newObject['DataType'] = 'Scale'
        
        self._skip(4)
        
        newObject['ScaleCentre'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['ScaleCentre'][0, colIdx] = self._readDouble()
        
        varNames = ['xScale', 'yScale', 'zScale']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opRotPoint(self, fileName = None):
        # Opcode 80
        newObject = dict()
        newObject['DataType'] = 'RotateAboutPoint'
        
        self._skip(4)
        
        newObject['RotationCentre'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['RotationCentre'][0, colIdx] = self._readDouble()
        
        varNames = ['iAxis', 'jAxis', 'kAxis', 'Angle']
        for varName in varNames:
            newObject[varName] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opRotScPoint(self, fileName = None):
        # Opcode 81
        newObject = dict()
        newObject['DataType'] = 'RotateScaleToPoint'
        
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
    
    
    def _opPut(self, fileName = None):
        # Opcode 82
        newObject = dict()
        newObject['DataType'] = 'Put'
        
        self._skip(4)
        
        varNames = ['FromOrigin', 'FromAlign', 'FromTrack', 'ToOrigin', 'ToAlign', 'ToTrack']
        
        for varName in varNames:
            newObject[varName] = np.zeros((1, 3))
            for colIdx in range(3):
                newObject[varName][0, colIdx] = self._readDouble()
        
        self._addObject(newObject)
    
    def _opEyeTrackPalette(self, fileName = None):
        # Opcode 83
        newObject = dict()
        newObject['DataType'] = 'EyepointAndTrackplanePalette'
        
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
    
    
    def _opMesh(self, fileName = None):
        # Opcode 84
        newObject = dict()
        newObject['DataType'] = 'Mesh'
        
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
        
        
    
    
    def _opLocVertexPool(self, fileName = None):
        # Opcode 85
        pass
    
    
    def _opMeshPrim(self, fileName = None):
        # Opcode 86
        pass
    
    
    def _opRoadSeg(self, fileName = None):
        # Opcode 87
        newObject = dict()
        newObject['DataType'] = "RoadSegment"
        newObject['ASCIIID'] = self._readString(8)
        
        self._addObject(newObject)
    
    
    def _opRoadZone(self, fileName = None):
        # Opcode 88
        newObject = dict()
        newObject['DataType'] = 'RoadZone'
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
    
    
    def _opMorphVertex(self, fileName = None):
        # Opcode 89
        pass
    
    
    def _opLinkPalette(self, fileName = None):
        # Opcode 90
        pass
    
    
    def _opSound(self, fileName = None):
        # Opcode 91
        newObject = dict()
        newObject['DataType'] = 'Sound'
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
    
    
    def _opRoadPath(self, fileName = None):
        # Opcode 92
        newObject = dict()
        newObject['DataType'] = 'RoadPath'
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
    
    
    def _opSoundPalette(self, fileName = None):
        # Opcode 93
        newObject = dict()
        newObject['DataType'] = 'SoundPaletteData'
        
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
    
    def _opGenMatrix(self, fileName = None):
        # Opcode 94
        # This is the same as the matrix command, so call the matrix function
        self._opMatrix(fileName)
    
    
    def _opText(self, fileName = None):
        # Opcode 95
        newObject = dict()
        newObject['DataType'] = 'Text'
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
    
    
    def _opSwitch(self, fileName = None):
        # Opcode 96
        newObject = dict()
        newObject['DataType'] = 'Switch'
        
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
    
    
    def _opLineStylePalette(self, fileName = None):
        # Opcode 97
        newObject = dict()
        newObject['DataType'] = 'LineStylePalette'
        newObject['LineStyleIdx'] = self._readUShort()
        newObject['PatternMask'] = self._readUShort()
        newObject['LineWidth'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opClipRegion(self, fileName = None):
        # Opcode 98
        newObject = dict()
        newObject['DataType'] = 'ClipRegion'
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
    
    
    def _opExtension(self, fileName = None):
        # Opcode 100
        newObject = dict()
        newObject['DataType'] = 'Extension'
        
        RecordLength = self._readUShort()
        
        varNames = ['ASCIIID', 'SiteID']
        for varName in varNames:
            newObject[varName] = self._readString(8)
        
        self._skip(1)
        
        newObject['Revision'] = self._readSChar()
        newObject['RecordCode'] = self._readUShort()
        
        newObject['ExtendedData'] = self._readString(RecordLength - 24)
        
        self._addObject(newObject)
    
    
    def _opLightSrc(self, fileName = None):
        # Opcode 101
        newObject = dict()
        newObject['DataType'] = 'LightSource'
        
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
    
    
    def _opLightSrcPalette(self, fileName = None):
        # Opcode 102
        newObject = dict()
        newObject['DataType'] = 'LightSourcePalette'
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
    
    
    def _opBoundSphere(self, fileName = None):
        # Opcode 105
        newObject = dict()
        newObject['DataType'] = 'BoundingSphere'
        
        # Skip over the reserved area
        self._skip(4)
        
        newObject['Radius'] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundCylinder(self, fileName = None):
        # Opcode 106
        newObject = dict()
        newObject['DataType'] = 'BoundingCylinder'
        
        # Skip over the reserved area
        self._skip(4)
        
        newObject['Radius'] = self._readDouble()
        newObject['Height'] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundConvexHull(self, fileName = None):
        # Opcode 107
        newObject = dict()
        newObject['DataType'] = 'BoundingConvexHull'
        
        RecordLength = self._readUShort()
        newObject['NumberOfTriangles'] = self._readUInt()
        
        newObject['Vertex1'] = []
        newObject['Vertex2'] = []
        newObject['Vertex3'] = []
        
        # Read the vertex records:
        for triangleIdx in range((RecordLength / 8) - 1):
            for vertexIdx in range(1, 4):
                # Represent x, y and z
                tempVector = np.zeros((1, 3))
                for colIdx in range(3):
                    tempVector[0, colIdx] = self._readDouble()
                # Add this to the appropriate vector index
                newObject['Vertex' + str(vertexIdx)].append(tempVector)
        
        # 65528 = Header (8) + (9*8) * 910; Continuation record = 65528 - 4:
        while RecordLength >= 65524:
            # Check to see if the next record is a continuation record:
            iRead = self._readUShort()
            
            if iRead != 23:
                # This is not a continuation record. Reverse and save variable
                self._skip(-2)
                break
            # This is a continuation record, so get the record length
            RecordLength = self._readUShort()
            
            # Now continue appending to variable
            for triangleIdx in range((RecordLength - 4) / 8):
                for vertexIdx in range(1, 4):
                    # Represent x, y and z:
                    tempVector = np.zeros((1, 3))
                    for colIdx in range(3):
                        tempVector[0, colIdx] = self._readDouble()
                    newObject['Vertex' + str(vertexIdx)].append(tempVector)
        
        self._addObject(newObject)
    
    
    def _opBoundVolCentre(self, fileName = None):
        # Opcode 108
        newObject = dict()
        newObject['DataType'] = 'BoundingVolumeCentre'
        
        # Skip over the reserved area
        self._skip(4)
        
        Axes = ['x', 'y', 'z']
        
        for axis in Axes:
            newObject[axis] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    
    def _opBoundVolOrientation(self, fileName = None):
        # Opcode 109
        newObject = dict()
        newObject['DataType'] = 'BoundingVolumeOrientation'
        
        # Skip over the reserved area
        self._skip(4)
        
        Angles = ['Yaw', 'Pitch', 'Roll']
        
        for angle in Angles:
            newObject[angle] = self._readDouble()
        
        # Finally, add the object to the stack
        self._addObject(newObject)
    
    def _opLightPt(self, fileName = None):
        # Opcode 111
        newObject = dict()
        newObject['DataType'] = 'LightPoint'
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
    
    
    def _opTextureMapPalette(self, fileName = None):
        # Opcode 112
        newObject = dict()
        newObject['DataType'] = 'TextureMappingPalette'
        
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
    
    def _opMatPalette(self, fileName = None):
        # Opcode 113
        newObject = dict()
        newObject['DataType'] = "MaterialPalette"
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
        RecordLength = self._readUShort()
        
        # And as the contents of the record is "reserved for use by Multigen-Paradigm",
        # then skip to the end of the record
        self._skip(RecordLength - 4)
    
    
    def _opPushAttr(self, fileName = None):
        # Opcode 122
        pass
    
    
    def _opPopAttr(self, fileName = None):
        # Opcode 123
        pass
    
    
    def _opCurve(self, fileName = None):
        # Opcode 126
        newObject = dict()
        newObject['DataType'] = 'Curve'
        
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
    
    
    def _opRoadConstruc(self, fileName = None):
        # Opcode 127
        newObject = dict()
        newObject['DataType'] = 'RoadConstruction'
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
    
    
    def _opLightPtAppearPalette(self, fileName = None):
        # Opcode 128
        newObject = dict()
        newObject['DataType'] = 'LightPointAppearancePalette'
        
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
    
    
    def _opLightPtAnimatPalette(self, fileName = None):
        # Opcode 129
        newObject = dict()
        newObject['DataType'] = 'LightPointAnimationPalette'
        
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
    
    
    def _opIdxLightPt(self, fileName = None):
        # Opcode 130
        newObject = dict()
        newObject['DataType'] = 'IndexedLightPoint'
        
        newObject['ASCIIID'] = self._readString(8)
        
        varNames = ['AppearanceIndex', 'AnimationIndex', 'DrawOrder']
        for varName in varNames:
            newObject[varName] = self._readInt()
        
        # Skip over reserved area:
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opLightPtSys(self, fileName = None):
        # Opcode 131
        newObject = dict()
        newObject['DataType'] = 'LightPointSystem'
        newObject['ASCIIID'] = self._readString(8)
        newObject['Intensity'] = self._readFloat()
        
        newObject['AnimationState'] = self._readUInt()
        if newObject['AnimationState'] not in [0, 1, 2]:
            raise Exception('Unable to determine animation state.')
        
        newObject['Flags'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opIdxStr(self, fileName = None):
        # Opcode 132
        newObject = dict()
        
        RecordLength = self._readUShort()
        newObject['DataType'] = 'IndexedString'
        newObject['Index'] = self._readUInt()
        newObject['ASCIIString'] = self._readString(RecordLength - 8)
        
        self._addObject(newObject)
    
    
    def _opShaderPalette(self, fileName = None):
        # Opcode 133
        newObject = dict()
        newObject['DataType'] = 'ShaderPalette'
        
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
    
    
    def _opExtMatHdr(self, fileName = None):
        # Opcode 135
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialHeader'
        
        newObject['MaterialIndex'] = self._readUInt()
        newObject['MaterialName'] = self._readString(12)
        newObject['Flags'] = self._readUInt()
        
        newObject['ShadeModel'] = self._readUInt()
        if newObject['ShadeModel'] not in [0, 1, 2]:
            raise Exception("Unable to determine shade model.")
            
        self._addObject(newObject)
    
    
    def _opExtMatAmb(self, fileName = None):
        # Opcode 136
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialAmbient'
        
        newObject['AmbientColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['AmbientColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatDif(self, fileName = None):
        # Opcode 137
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialDiffuse'
        
        newObject['DiffuseColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['DiffuseColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatSpc(self, fileName = None):
        # Opcode 138
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialSpecular'
        
        newObject['Shininess'] = self._readFloat()
        
        newObject['SpecularColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['SpecularColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatEms(self, fileName = None):
        # Opcode 139
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialEmissive'
        
        newObject['EmissiveColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['EmissiveColour'][0, colIdx] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatAlp(self, fileName = None):
        # Opcode 140
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialAlpha'
        
        newObject['Alpha'] = self._readFloat()
        
        varNames = ['TextureIndexLayer', 'UVSetLayer']
        
        for layerIdx in range(4):
            for varName in varNames:
                newObject[varName + str(layerIdx)] = self._readUInt()
        
        newObject['Quality'] = self._readUInt()
        if newObject['Quality'] not in [0, 1]:
            raise Exception("Unable to determine quality.")
        
        self._addObject(newObject)
    
    
    def _opExtMatLightMap(self, fileName = None):
        # Opcode 141
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialLightMap'
        
        newObject['MaximumIntensity'] = self._readFloat()
        
        varNames = ['TextureIndex', 'UVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatNormMap(self, fileName = None):
        # Opcode 142
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialNormalMap'
        
        varNames = ['TextureIndex', 'UVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatBumpMap(self, fileName = None):
        # Opcode 143
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialBumpMap'
        
        varNames = ['TextureIndex', 'UVSet', 'TangentUVSet', 'BinormalUVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatShadowMap(self, fileName = None):
        # Opcode 145
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialShadowMap'
        
        newObject['MaximumIntensity'] = self._readFloat()
        
        varNames = ['TextureIndex', 'UVSet']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtMatReflMap(self, fileName = None):
        # Opcode 147
        newObject = dict()
        newObject['DataType'] = 'ExtendedMaterialReflectionMap'
        
        newObject['TintColour'] = np.zeros((1, 3))
        for colIdx in range(3):
            newObject['TintColour'][0, colIdx] = self._readFloat()
        
        varNames = ['ReflectionTextureIndex', 'ReflectionUVSet', 'EnvironmentTextureIndex']
        for varName in varNames:
            newObject[varName] = self._readUInt()
        
        # Skip over reserved area
        self._skip(4)
        
        self._addObject(newObject)
    
    
    def _opExtGUIDPalette(self, fileName = None):
        # Opcode 148
        newObject = dict()
        newObject['DataType'] = 'ExtensionGUIDPalette'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        
        # Documentation says that this is a 40 byte integer. I imply it's an integer (4 bytes) * 10.
        newObject['GUIDString'] = []
        for idx in range(10):
            newObject['GUIDString'].append(self._readUInt())
        
        self._addObject(newObject)
    
    
    def _opExtFieldBool(self, fileName = None):
        # Opcode 149
        newObject = dict()
        newObject['DataType'] = 'ExtensionFieldBoolean'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldBoolean'] = self._readUInt()
        
        self._addObject(newObject)
    
    
    def _opExtFieldInt(self, fileName = None):
        # Opcode 150
        newObject = dict()
        newObject['DataType'] = 'ExtensionFieldInteger'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldInteger'] = self._readInt()
        
        self._addObject(newObject)
    
    
    def _opExtFieldFloat(self, fileName = None):
        # Opcode 151
        newObject = dict()
        newObject['DataType'] = 'ExtensionFieldFloat'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldFloat'] = self._readFloat()
        
        self._addObject(newObject)
    
    
    def _opExtFieldDouble(self, fileName = None):
        # Opcode 152
        newObject = dict()
        newObject['DataType'] = 'ExtensionFieldDouble'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['ExtensionFieldDouble'] = self._readDouble()
        
        self._addObject(newObject)
    
    
    def _opExtFieldString(self, fileName = None):
        # Opcode 153
        newObject = dict()
        RecordLength = self._readUShort()
        newObject['DataType'] = 'ExtensionFieldString'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['StringLength'] = self._readUInt()
        newObject['ExtensionFieldString'] = self._readString(RecordLength - 12)
        
        # Check to see if there's a continuation (assuming this string is full)
        while RecordLength == 0xffff:
            iRead = self._readUShort()
            
            # Check for continuation Opcode
            if iRead != 23:
                # Not a continuation record. Rewind and return
                self._skip(-2)
                break
            
            # If here, this is a continuation record.
            RecordLength = self._readUShort()
            
            newObject['ExtensionFieldString'] += self._readString(RecordLength - 4)
        
        self._addObject(newObject)
    
    
    def _opExtFieldXMLString(self, fileName = None):
        # Opcode 154
        newObject = dict()
        RecordLength = self._readUShort()
        newObject['DataType'] = 'ExtensionFieldXMLString'
        newObject['GUIDPaletteIdx'] = self._readUInt()
        newObject['StringLength'] = self._readUInt()
        newObject['ExtensionFieldXMLString'] = self._readString(RecordLength - 12)
        
        # Check to see if there's a continuation (assuming this string is full)
        while RecordLength == 0xffff:
            iRead = self._readUShort()
            
            # Check for continuation Opcode
            if iRead != 23:
                # Not a continuation record. Rewind and return
                self._skip(-2)
                break
            
            # If here, this is a continuation record.
            RecordLength = self._readUShort()
            
            newObject['ExtensionFieldXMLString'] += self._readString(RecordLength - 4)
        
        self._addObject(newObject)
    
