"""Meaningful negative checks for the demonstration's input/output contract."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent

class DemoContract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="pharma-deck-contract-")
        self.base=Path(self.temp.name)
        self.fixture=json.loads((HERE/"examples/analysis.json").read_text(encoding="utf-8"))
    def tearDown(self):
        self.temp.cleanup()
    def invoke(self,data,output):
        source=self.base/"analysis.json"
        source.write_text(json.dumps(data),encoding="utf-8")
        return subprocess.run([sys.executable,str(HERE/"build_preclinical_demo.py"),"--analysis",str(source),"--output",str(output)],capture_output=True,text=True,encoding="utf-8",errors="replace")
    def test_rejects_real_data_claim(self):
        self.fixture["data_kind"]="real-preclinical-data"
        target=self.base/"target"
        self.assertNotEqual(self.invoke(self.fixture,target).returncode,0)
        self.assertFalse(target.exists())
    def test_rejects_conflicting_group_and_comparison(self):
        self.fixture["efficacy"]["groups"]["high"]["mean_mm3"]+=30
        target=self.base/"target"
        result=self.invoke(self.fixture,target)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("Input comparison differs from input group means",result.stderr)
        self.assertFalse(target.exists())
    def test_preserves_existing_project(self):
        target=self.base/"target"
        target.mkdir()
        marker=target/"owned.txt"
        marker.write_bytes(b"existing user file")
        result=self.invoke(self.fixture,target)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(marker.read_bytes(),b"existing user file")
        self.assertEqual(list(target.iterdir()),[marker])
    def test_rejects_failed_pk(self):
        self.fixture["pk"]["exit_code"]=1
        target=self.base/"target"
        result=self.invoke(self.fixture,target)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("PK upstream analysis is incomplete",result.stderr)
        self.assertFalse(target.exists())

if __name__=="__main__":
    unittest.main()
