#!/usr/bin/env python3

#     Copyright 2016 Stephen Sinclair

#     Licensed under the Apache License, Version 2.0 (the "License"); you may not
#     use this file except in compliance with the License. You may obtain a copy
#     of the License at

#         http://www.apache.org/licenses/LICENSE-2.0

#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#     WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#     License for the specific language governing permissions and limitations
#     under the License.

from __future__ import print_function, unicode_literals
from builtins import bytes

from lxml import etree
import sys, os, bz2

if len(sys.argv) < 2:
    input_filename = 'siconos-srcml.xml.bz2'
    output_filename = 'siconos-srcml.mse.bz2'
else:
    input_filename = sys.argv[1]
    ext = os.path.splitext(input_filename)
    if ext[1] in ['.bz2', '.gzip']:
        output_filename = os.path.splitext(ext[0])[0]
        bz = bz2.BZ2File
        bzext = '.bz2'
    else:
        output_filename = ext[0]
        bz = open
        bzext = ''
    output_filename += '.mse' + bzext

package_name = 'Siconos'
if len(sys.argv) >= 4:
    if sys.argv[2] == '--package':
        package_name = sys.argv[3]
    else:
        print('Unknown option "{}"'.format(sys.argv[2]))
        sys.exit(1)

print('Loading',input_filename,'...')
tree = etree.parse(bz(input_filename))

ns = {'src': u'http://www.srcML.org/srcML/src',
      'cpp': u'http://www.srcML.org/srcML/cpp'}

id_counter=0

class mseRef(object):
    def __init__(self, ref):
        self.ref = ref
    def __str__(self):
        return "(ref: %d)"%self.ref.id

class mseId(object):
    def __init__(self, val_id):
        self.value = val_id
    def __str__(self):
        return "(id: %d)"%self.value

class mseString(object):
    def __init__(self, s):
        self.string = s
        if self.string is not None and "'" in self.string:
            raise ValueError('mseString contains "\'": "%s"'%self.string)
    def __str__(self):
        return "'%s'"%self.string

class mseBoolean(object):
    def __init__(self, b):
        self.value = b
    def __str__(self):
        return ['false','true'][self.value]

class mseInteger(object):
    def __init__(self, i):
        self.value = i
    def __str__(self):
        return str(self.value)

class Node(object):
    def __init__(self, mse_node_type):
        global id_counter
        self.id = id_counter
        self.mse_node_type = mse_node_type
        self.sourceAnchor = None
        id_counter += 1
    def add_sourceAnchor(self, unit, startline=None, endline=None):
        fa = FileAnchor(self, unit, startline, endline)
        self.sourceAnchor = fa
        nodes.append(fa)
    def add_sourceUnitXML(self, xml):
        unit = xml.xpath('./ancestor::src:unit[@filename][1]', namespaces=nspc)
        if unit is not None and len(unit)>0:
            try:
                u = units_by_path[unit[0].attrib['filename']]
                self.add_sourceAnchor(u,
                                      startline=None, # TODO, possible from SrcML?
                                      endline=None)
            except KeyError:
                print('Could not resolve sourceAnchor', unit[0].attrib['filename'],
                      'for', self.id)
    def to_mse(self):
        attribs = self.mse_attribs()
        if self.sourceAnchor is not None:
            attribs.append(('sourceAnchor', mseRef(self.sourceAnchor)))
        mse = '\t(%s '%self.mse_node_type
        mse += str(mseId(self.id))
        for name, val in attribs:
            mse += '\n\t\t(%s %s)'%(name, str(val))
        mse += ')'
        return mse

class Package(Node):
    def __init__(self, name):
        Node.__init__(self, 'FAMIX.Package')
        self.name = name
    def mse_attribs(self):
        return [('name', mseString(self.name))]

class CompilationUnit(Node):
    def __init__(self, filepath, lang):
        Node.__init__(self, 'FAMIX.CompilationUnit')
        self.filepath = filepath
        self.filename = os.path.split(filepath)[1]
        self.language = lang
        self.includes = []
    def add_include(self, header):
        i = Include(self, header)
        self.includes.append(i)
        nodes.append(i)
    def mse_attribs(self):
        return [('filepath', mseString(self.filepath)),
                ('name', mseString(self.filename)),
                ('language', mseString(self.language))]

class Header(Node):
    def __init__(self, filepath, lang):
        Node.__init__(self, 'FAMIX.Header')
        self.filepath = filepath
        self.filename = os.path.split(filepath)[1]
        self.language = lang
        self.includes = []
    def add_include(self, header):
        i = Include(self, header)
        self.includes.append(i)
        nodes.append(i)
    def mse_attribs(self):
        return [('filepath', mseString(self.filepath)),
                ('name', mseString(self.filename)),
                ('language', mseString(self.language))]

class Include(Node):
    def __init__(self, includingfile, includedfile):
        Node.__init__(self, 'FAMIX.Include')
        self.includingfile = includingfile
        self.includedfile = includedfile
    def mse_attribs(self):
        return [('source', mseRef(self.includingfile)),
                ('target', mseRef(self.includedfile))]

class FileAnchor(Node):
    def __init__(self, element, unit, startline=None, endline=None):
        Node.__init__(self, 'FAMIX.FileAnchor')
        self.element = element
        self.unit = unit
        self.startline = startline
        self.endline = endline
    def mse_attribs(self):
        result = [('element', mseRef(self.element)),
                  ('unit', mseRef(self.unit)),
                  ('fileName', mseString(self.unit.filename))]
        if self.startline is not None:
            result.append(('startLine', mseInteger(self.startline)))
        if self.endline is not None:
            result.append(('endLine', mseInteger(self.endline)))
        return result

class Class(Node):
    def __init__(self, package, name):
        Node.__init__(self, 'FAMIX.Class')
        self.package = package
        self.name = name
        self.methods = []
        self.variables = []
        self.sourceAnchor = None
        self.supers = []
        self.inheritances = {}
    def add_method(self, name, sig, returnType=None):
        met = Method(name, self, sig, returnType)
        self.methods.append(met)
        nodes.append(met)
    def add_variable(self, name, typename):
        attr = Attribute(name, typename, self)
        self.variables.append(attr)
        nodes.append(attr)
    def add_superclass(self, name):
        self.supers.append(name)
    def add_inheritance(self, superclass):
        inh = Inheritance(self, superclass)
        self.inheritances[superclass.name] = inh
        nodes.append(inh)
    def add_call(self, name, args):
        pass
    def mse_attribs(self):
        return [('name', mseString(self.name)),
                ('belongsToPackage', mseRef(self.package))]

class Inheritance(Node):
    def __init__(self, subclass, superclass):
        Node.__init__(self, 'FAMIX.Inheritance')
        self.subclass = subclass
        self.superclass = superclass
    def mse_attribs(self):
        return [('subclass', mseRef(self.subclass)),
                ('superclass', mseRef(self.superclass))]

class Method(Node):
    def __init__(self, name, classclass, signature, returnType=None):
        Node.__init__(self, 'FAMIX.Method')
        self.declaredType = None
        if returnType is not None:
            self.declaredType = UnresolvedType(returnType, self)
        self.name = name
        self.classclass = classclass
        self.signature = signature
    def mse_attribs(self):
        result = [('name', mseString(self.name)),
                  ('signature', mseString(self.signature)),
                  ('parentType', mseRef(self.classclass))]
        decl = self.declaredType
        if decl is not None and not type(decl)==UnresolvedType:
            result.append(('declaredType', mseRef(self.declaredType)))
        return result

class Attribute(Node):
    def __init__(self, name, declaredType, classclass):
        Node.__init__(self, 'FAMIX.Attribute')
        self.name = name
        self.declaredType = UnresolvedType(declaredType, self)
        self.classclass = classclass
    def mse_attribs(self):
        result = [('name', mseString(self.name)),
                  ('parentType', mseRef(self.classclass))]
        decl = self.declaredType
        if decl is not None and not type(decl)==UnresolvedType:
            result.append(('declaredType', mseRef(self.declaredType)))
        return result

class Function(Node):
    def __init__(self, name, signature, returnType=None):
        Node.__init__(self, 'FAMIX.Function')
        self.name = name
        self.signature = signature
        self.declaredType = None
        if returnType is not None:
            self.declaredType = UnresolvedType(returnType, self)
    def mse_attribs(self):
        result = [('name', mseString(self.name)),
                  ('signature', mseString(self.signature))]
        decl = self.declaredType
        if decl is not None and not type(decl)==UnresolvedType:
            result.append(('declaredType', mseRef(self.declaredType)))
        return result

class Invocation(Node):
    def __init__(self, signature, sender, receiver=None):
        Node.__init__(self, 'FAMIX.Invocation')
        self.signature = signature
        if "'" in self.signature:
            raise ValueError('Invocation signature contains "\'": "%s"'%self.signature)
        self.sender = sender
        self.receiver = receiver
    def mse_attribs(self):
        result = [('signature', mseString(self.signature)),
                  ('sender', mseRef(self.sender))]
        if self.receiver is not None:
            results.append(('receiver', mseRef(self.receiver)))
        return result

class UnresolvedType(Node):
    def __init__(self, name, attr):
        Node.__init__(self, None)
        self.name = name
        self.attr = attr
        unresolved.append(self)
    def resolve(self, classclass):
        self.attr.declaredType = classclass

def make_signature(name, args, ty=None, removeQuote=False):
    etree.strip_elements(args, '{*}comment')
    etree.strip_elements(args, '{*}init')
    signature = '%s%s'%(name.xpath('string()'),
                        args.xpath('string()'))
    if ty is not None:
        signature = '%s %s'%(ty.xpath('string()'),
                             signature)
    r = ['',"'"][removeQuote]
    if not removeQuote and "'" in signature:
        raise ValueError('Signature contains "\'": "%s"'%signature)
    return ' '.join(signature.replace(r,'').split())

# Reset collections
nodes = []
classes = {}
functions = {}
units_by_name = {}
units_by_path = {}
headers = {}
invocations = []
unresolved = []

# Find interesting parts of the SrcML XML
siconos = Package(package_name)
nodes.append(siconos)

for unit in tree.findall('//{*}unit'):
    path = unit.attrib['filename']
    lang = unit.attrib['language']
    ext = os.path.splitext(path)[1]
    if ext=='.i':
        lang = 'SWIG'
    if ext in ['.h', '.hpp', '.i']:
        u = Header(path, lang)
        headers[u.filename] = u
    else:
        u = CompilationUnit(path, lang)
    nodes.append(u)
    units_by_name[u.filename] = u
    units_by_path[u.filepath] = u
print('Found',len(units_by_name),'units')
print('Found',len(headers),'headers')

# Resolve #include relations
nspc = {'cpp': 'http://www.srcML.org/srcML/cpp',
        'src': 'http://www.srcML.org/srcML/src'}
n_includes = 0
n_unresolved_includes = 0
for unit in tree.findall('//{*}unit'):
    path = unit.attrib['filename']
    lang = unit.attrib['language']
    ext = os.path.splitext(path)[1]
    name = os.path.split(path)[1]
    if ext=='.i':
        lang = 'SWIG'
    if lang == 'SWIG':
        includes = unit.xpath(
            './/src:literal[following::src:name][following::src:operator]',
            namespaces=nspc)
        for i in includes:
            p = i.getprevious()
            if p is not None:
                p2 = p.getprevious()
                if (p2 is not None
                    and p.xpath('string()')=='include'
                    and p2.xpath('string()')=='%'):

                    fn = i.xpath('string()').split('"')
                    if len(fn)==3:
                        fn = fn[1]
                    elif len(fn)==1:
                        fn = fn[0]
                    u = None
                    try:
                        u = units_by_name[name]
                        h = units_by_name[fn]
                    except KeyError:
                        # make node for header marked as external?
                        h = None
                        n_unresolved_includes += 1
                    if u is not None and h is not None:
                        u.add_include(h)
                        n_includes += 1

    if lang in ('C','C++','SWIG'):
        includes = unit.xpath('.//cpp:include/cpp:file',namespaces=nspc)
        for i in includes:
            fn = i.xpath('string()')
            fn = fn.replace('>','').replace('<','').replace('"','')
            try:
                u = units_by_name[name]
                h = units_by_name[fn]
            except KeyError:
                # make node for header marked as external?
                u = None
                h = None
                n_unresolved_includes += 1
            if u is not None and h is not None:
                u.add_include(h)
                n_includes += 1
print('Resolved',n_includes,'includes')
print('Could not resolved',n_unresolved_includes,'includes (probably external libs)')

for cl in tree.findall('//{*}class'):
    p = cl.getparent()
    language = None
    while p is not None:
        if 'language' in p.attrib:
            language = p.attrib['language']
            break
        p = p.getparent()
    if language not in ('C', 'C++'):
        continue
    classname = cl.find('{*}name')
    if classname == None:
        continue
    node = Class(siconos, classname.text)
    supers = cl.findall('./{*}super/{*}name')
    decls = cl.findall('.//{*}decl/{*}name')
    methods = cl.findall('.//{*}function_decl')
    node.add_sourceUnitXML(cl)
    if supers:
        for s in supers:
            node.add_superclass(s.xpath('string()'))
    if methods:
        for m in methods:
            name = m.find('./{*}name')
            ty = m.find('./{*}type')
            args = m.find('./{*}parameter_list')
            signature = make_signature(name, args, ty)
            node.add_method(name.xpath('string()'),
                            signature,
                            ty.xpath('string()') if ty else None)
    if decls:
        for d in decls:
            typename = None
            if d.getprevious() is not None and 'type' in d.getprevious().tag:
                typeelem = d.getprevious().find('{*}name')
                if typeelem is not None:
                    names = typeelem.findall('{*}name')
                    if len(names)>1 and names[0].text == 'SP':
                        typename = names[-1].xpath('string()')
                    else:
                        typename = typeelem.xpath('string()')
            node.add_variable(d.xpath('string()'), typename)
    nodes.append(node)
    classes[classname.text] = node
print('Found',len(classes),'classes')

# Make inheritance nodes
for cl in classes.values():
    for s in cl.supers:
        if s in classes:
            cl.add_inheritance(classes[s])

# Find non-class functions
funcs = tree.findall('//{*}function')
if funcs:
    for func in funcs:
        cl = next((x for x in func.iterancestors()
                   if 'class' in x.tag), None)
        if cl is not None:
            continue
        name = func.find('./{*}name')
        if name is None:
            continue
        if name.xpath('string()')[0]=='$':  # skip some templates in LAPACK
            continue
        if (len(name.getchildren())==3
            and 'operator' in name.getchildren()[1].tag):
            if name.getchildren()[1].xpath('string()')=='::':
                continue
        args = func.find('./{*}parameter_list')
        if args is None:
            continue
        ty = func.find('./{*}type')
        if ty is not None:
            tyname = ty.xpath('string()')
        else:
            tyname = None
        signature = make_signature(name, args, ty, removeQuote=True)
        if signature not in functions:
            functions[signature] = Function(name.xpath('string()'),
                                            signature, tyname)
            nodes.append(functions[signature])
print('Found',len(functions),'non-class functions')

# Resolve unresolved types
count = 0
for t in unresolved:
    if t.name is not None:
        if t.name in classes:
            count += 1
            t.resolve(classes[t.name])
        # else:
        #     print 'Cannot resolve', repr(t.name)
print('Resolved',count,'types')

# Find function calls
calls = tree.findall('//{*}call')
if calls:
    for c in calls:
        name = c.find('./{*}name')
        args = c.find('./{*}argument_list')
        unit = next((x for x in c.iterancestors()
                     if 'unit' in x.tag), None)
        if unit is None or unit.attrib['filename'][-2:]=='.i':
            continue
        cl = next((x for x in c.iterancestors()
                   if 'class' in x.tag), None)
        func = next((x for x in c.iterancestors()
                     if 'function' in x.tag), None)
        sender = None
        if cl is not None:
            # In a class definition
            # Find the class and sender is the method
            clname = cl.find('./{*}name')
            const = next((x for x in c.iterancestors()
                          if 'constructor' in x.tag), None)
            funcdecl = next((x for x in c.iterancestors()
                             if 'function' in x.tag), None)
            if clname is not None and clname.xpath('string()') in classes:
                cl = classes[clname.xpath('string()')]
                if const is not None:
                    pass #TODO constructors
                elif funcdecl is not None:
                    if funcdecl.find('{*}name') is not None:
                        methname = funcdecl.find('{*}name').xpath('string()')
                        method = next((x for x in cl.methods
                                       if x.name == methname), None)
                        sender = method
        elif func is not None:

            p = func
            while p is not None:
                if 'language' in p.attrib:
                    language = p.attrib['language']
                    break
                p = p.getparent()
            if language not in ('C','C++'):
                continue

            # In a function implementation: If implementation of a
            # method, find the class and sender is the method.
            # Otherwise, sender is the function, if found.
            caller_name = func.find('./{*}name')
            caller_args = func.find('./{*}parameter_list')
            caller_type = func.find('./{*}type')

            # skip some templates in LAPACK
            if caller_name.xpath('string()')[0]=='$':
                continue

            caller_sig = make_signature(caller_name, caller_args,
                                        caller_type)
            if caller_sig in functions:
                sender = functions[caller_sig]
            else:
                if (len(caller_name.getchildren())==3 and
                    caller_name.getchildren()[1].xpath('string()')=='::'):
                    class_name = caller_name.getchildren()[0].xpath('string()')
                    method_name = caller_name.getchildren()[2].xpath('string()')
                    if class_name in classes:
                        cl = classes[class_name]
                        sender = next((x for x in cl.methods
                                       if x.name==method_name), None)
        if sender:
            inv = Invocation(signature=c.xpath('string()').replace("'",''),
                             sender=sender)
            invocations.append(inv)
            nodes.append(inv)
print('Found',len(invocations),'invocations')

# Print MSE to output file
output_file = bz(output_filename, 'w')
output_file.write(bytes(u'(\n', 'UTF-8'))
for n in nodes:
    output_file.write(bytes(n.to_mse(), 'UTF-8'))
    output_file.write(bytes(u'\n', 'UTF-8'))
output_file.write(bytes(u')\n', 'UTF-8'))
del output_file
