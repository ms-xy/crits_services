
# configuration parameter for MemoryEfficientFile::find, 500MB default
BIGFILE_MAX_CHUNKSIZE = 500 * (10**6)

class MemoryEfficientFile (object):
    """
    Low memory footprint file-like object. (read only access)
    Reading and finding does not advance the offset.
    If you need to adjust the offset, use seek or seek_relative.
    """
    __slots__ = ["file", "datamap", "size", "offset"]
    def __init__ (self, gridfsproxy):
        self.file     = gridfsproxy
        self.offset   = 0
    
    def close (self):
        del(self.file)
        del(self.offset)
        del(self)
    
    # provide base functionality
    def read (self, start, stop):
        if start is None or start < 0:
            start = 0
        if stop is None or stop > self.size:
            stop = self.size
        if start >= self.size:
            start = self.size - 1
        if stop > self.size:
            stop = self.size
        self.file.seek(self.offset+start)
        return self.file.read(stop-start)
    
    def seek (self, offset):
        self.offset = offset
    def seek_relative (self, offset):
        self.seek(self.offset + offset)
    def tell (self):
        return self.offset
    
    def find (self, needle, offset=0):
        global BIGFILE_MAX_CHUNKSIZE
        size = len(needle)
        maxchunksize = min(max(2*size, BIGFILE_MAX_CHUNKSIZE), self.size)  # optimizable? @cvp
        chunkstart = self.offset + 0
        
        while chunkstart <= self.size:
            self.file.seek(chunkstart)
            
            chunksize  = min(self.size-chunkstart, maxchunksize)
            data = self.file.read(chunksize)
            result = data.find(needle)
            del(data)
            
            if result >= 0:
                # return result relative to offset (respect subfiles)
                result = chunkstart+result-self.offset
                return result
            chunkstart = chunkstart + chunksize - size
        return -1
        
        
    def startswith (self, needle):
        return self[0:len(needle)] == needle
    
    def subfile (self, start):
        class MemoryEfficientSubFile (MemoryEfficientFile):
            def __init__ (self, file, start):
                self.file     = file
                self.offset   = start
            def subfile (self, start):
                pass  # remove subfile ability
        return MemoryEfficientSubFile(self.file, self.offset+start)
    
    # provide interface for built-ins
    def __getitem__ (self, key):
        if isinstance(key, slice):
            return self.read(key.start, key.stop)
        else:
            return self.read(key.start, key.start+1)
    
    def __len__ (self):
        return self.file.gridout.getLength()
    @property
    def size (self):
        return len(self)