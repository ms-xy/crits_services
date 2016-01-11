from crits.services.core import Service, ServiceConfigError
from zip_meta import ZipParser
from filewrapper import FileWrapper

class ZipMetaService(Service):
    """
    Parses meta data from Zip Files using a custom parser.
    """

    name = "zip_meta"
    version = '1.0.0'
    description = "Generate metadata from zip files."
    supported_types = ['Sample']

    @staticmethod
    def valid_for(obj):
        # Only run on zip files
        if obj.filedata.grid_id is None:
            raise ServiceConfigError("Missing filedata.")
        
        # read the magic
        magic = obj.filedata.read(4)
        # Reset the read pointer.
        obj.filedata.seek(0)

        if len(magic) < 4:
            raise ServiceConfigError("Not enough filedata.")

        if magic not in [ZipParser.zipLDMagic, ZipParser.zipCDMagic]:
            raise ServiceConfigError("Not a zip file.")

    def run(self, obj, config):
        zparser = ZipParser(FileWrapper(obj.filedata))
        parsedZip =  zparser.parseZipFile()
        if not parsedZip:
            self._error("Could not parse document as a zip file")
            return
        for cd in parsedZip:
            for name,value in cd.iteritems():
                if name == 'ZipExtraField':
                    continue
                name = {"Name" : name}
                if type(value) is list or type(value) is tuple:
                    for element in value:
                        self._add_result(cd["ZipFileName"], str(element), name)
                # Add way to handle dictionary.
                #if type(value) is dict: ...
                else:
                    self._add_result(cd["ZipFileName"], str(value), name)
            if cd["ZipExtraField"]:
                for dictionary in cd["ZipExtraField"]:
                    if dictionary["Name"] == "UnknownHeader":
                        for name,value in dictionary.iteritems():
                            name = {"Name" : name}
                            if name == "Data":
                                self._add_result(dictionary["Name"], name, name)
                            else:
                                self._add_result(dictionary["Name"], str(value), name)
                    else:
                        for name,value in dictionary.iteritems():
                            name = {"Name" : name}
                            self._add_result(dictionary["Name"], str(value), name)
            else:
                name = {"Name" : "ExtraField"}
                self._add_result(cd["ZipFileName"], "None", name)

    def _parse_error(self, item, e):
        self._error("Error parsing %s (%s): %s" % (item, e.__class__.__name__, e))
