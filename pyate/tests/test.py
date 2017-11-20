import unittest
import visawrapper

class TestImports(unittest.TestCase):
    def testImportWanglib(self):
        import wanglib.prologix

    def testImportVisawrapper(self):
        import visawrapper

    def testImportPate(self):
        import pate

class TestWrapper(unittest.TestCase):

    def setup(self):
        pass
        
    def testCreateResource(self):
        instr = visawrapper.ResourceManager.open_resource('PROLOGIX::172.29.92.133::1234::13')
        result = instr.query('*IDN?')
        print(result)
        instr.close()
       
if __name__ == '__main__':
    unittest.main()