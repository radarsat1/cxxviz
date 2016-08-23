# Tools for analysis and visualization of C++ code

These are some interim tools designed to translate output from C++
analysers into a format possible to use with visualisation tools such
as [Moose](http://www.moosetechnology.org/).

They remain somewhat unpolished and still contain things specific to
the project this was developed to analyse
([Siconos](http://siconos.gforge.inria.fr/)), stay tuned for some
instructions and examples.

## SrcML to MSE converter

Find some entities in SrcML output for C++ (classes, functions,
variable, etc.) and outputs them in MSE format.

Usage:

~~~
./srcml-to-mse.py <filename.xml.bz2>
~~~

where `filename.xml.bz2` is the output of running
[SrcML](http://www.srcml.org/) on a C++ tarball.  (I use `bz2` to the
output after running SrcML, but you don't have to.)

### Dependencies

Requires Python 3 and `lxml` to be installed.  Or, if you are using a
default Mac install and don't want to install a custom Python, the
following should work:

~~~
$ easy_install --upgrade --user .
~~~

This should read `setup.py` and install the `lxml` and `future`
packages for you.  You should then run the script, specifying Python
manually:

~~~
$ python srcml-to-mse.py <filename.xml.bz2>
~~~

Note, the use of bzip2 to make the SrcML output a bit smaller is
optional.  If used, the MSE output will also be compressed.

# Author

Stephen Sinclair <stephen.sinclair@inria.cl>

# Copyright

Apache 2.0.  See COPYING.md for more information.
