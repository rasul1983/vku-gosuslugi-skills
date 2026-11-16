import unittest,tempfile,json,importlib.util,zipfile,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
def module(name):
 spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
boot=module('bootstrap');docs=module('validate_package')
class Helpers(unittest.TestCase):
 def test_inventory_does_not_modify_source_and_refuses_overwrite(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);src=root/'service.json';src.write_text(json.dumps({'screens':[{'id':'s1','header':'Старт'}],'screenRules':{},'cycledScreenRules':{'s1':[{'nextDisplay':None}]}}));raw=src.read_bytes()
   out=boot.prepare('https://example.test/form',str(src),str(root/'tests'))
   self.assertEqual(src.read_bytes(),raw);self.assertFalse(json.loads((out/'vku.config.json').read_text())['mutations']['send']);self.assertIn('s1',json.loads((out/'inventory.json').read_text())['cycledScreenRules'])
   with self.assertRaises(ValueError):boot.prepare('https://example.test/form',str(src),str(out))
 def test_rejects_nonweb_url_and_duplicate_ids(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'x.json';p.write_text('{"screens":[{"id":"s1"},{"id":"s1"}]}')
   with self.assertRaises(ValueError):boot.prepare('file:///tmp',str(p),str(Path(tmp)/'out'))
   with self.assertRaises(ValueError):boot.prepare('https://example.test',str(p),str(Path(tmp)/'out'))
 def test_archive_traversal_and_ambiguous_names(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'bad.zip'
   for entries in [[('../attach.xml','<x/>')],[('one/attach.xml','<x/>'),('two/attach.xml','<x/>')]]:
    with zipfile.ZipFile(p,'w')as z:
     for n,b in entries:z.writestr(n,b)
    with self.assertRaises(ValueError):docs.validate(p,['attach.xml'],Path(tmp)/'out')
 def test_xsd_rejects_boundary_and_original_package_is_unchanged(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);xsd=root/'schema.xsd';xsd.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="value"><xs:simpleType><xs:restriction base="xs:string"><xs:maxLength value="3"/></xs:restriction></xs:simpleType></xs:element></xs:schema>')
   p=root/'docs.zip'
   with zipfile.ZipFile(p,'w')as z:z.writestr('attach.xml','<value>four</value>')
   before=hashlib.sha256(p.read_bytes()).hexdigest();r=docs.validate(p,['attach.xml'],root/'out',xsd)
   self.assertFalse(r['ok']);self.assertTrue(r['errors']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),before)
if __name__=='__main__':unittest.main()
