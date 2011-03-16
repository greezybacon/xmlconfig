XML Config

The goal of xmlconfig is to make difficult and complex software 
configurations more flexible and manageable. There is some expense
in this added flexibility, as xml configurations can be wordier and
more obscure than traditional configuration mechanisms. This document
aims to cover the general concepts in hopes of peaking your interest.

Documents
=========
As with any XML format, your configuration will be placed inside an xml
document. The parser for the xmlconfig is flexible enough that you can
include your xml configuration inside an existing xml document if you 
would like. Otherwise, I recommend using a document with a root element
of ``<config>``. The parser does not specifically look for ``<config>``
elements, instead it will look for ``<constants>`` elements. These 
elements will be the only content of the root element. You can specify
more than one if you like, optionally specifying different namespaces for
the enclosed constants. More on this in the namespaces section. A basic
configuration document might look like::

  <config>
      <constants>
          <!-- This is necessary for some reason I cannot remember
               -->
          <string key="intro">We are the knights who say "Ni!"</string>
      </constants>
  </config>

Basic Types
===========
Most basic types are supported out of the box

* Strings and binary data
* Integers and floating numbers
* Boolean values (0, nonzero, True, and False)
* Lists (with configurable delimiter)

The engine will parse the data of these elements and return data of the
specific type. So string elements return str types, float elements return
a Decimal types, snozberry elements return snozberry types, etc. This seems 
relatively intuitive and unnecessary to explicitly write out, but later 
we'll see why the type cannot always be easily inferred.

These simple constants are declared in the configuration like so::

  <config>
      <constants>
          <string key="string">This is a string</string>
          <float key="avagadro">6.023E+23</float>
          <int key="light">299792458</int>
          <bool key="debug">False</bool>
          <list key="knights">galahad,lancelot,bedevere,robin</list>
      </constants>
  </config>

Complex Types
=============
In an xml sense, complex types don't have textual content, they have other
xml elements as their content. Let's do some cool stuff with other xml
elements.

Sections
--------
Moving right along, more complex examples are possible with xmlconfig, the
simplest of which is the ``section`` type. The ``section`` type is basically
a ``dict`` or hastable, which in xmlconfig is used to group constants 
together. Sections are also nestable if you please. So for instance::

  <config>
      <constants>
          <section key="question1">
              <string key="question">What is you quest</string>
              <string key="answer">To seek the Holy Grail</string>
          </section>
      </constants>
  </config>
  
Currently, you can put constants of any type inside a ``section``, however,
you can only put a ``section`` in the root of a ``constants`` element or 
inside another ``section``. In other words, you cannot create a list of
sections, for instance.

Conditional Blocks
------------------
Another sweet tool is the concept of a value that depends on outside 
variables. These variables can be configured by your program before you
load the configuration document. For now, a ``hostname`` is magically 
declared for you. 

To create a constant that depends on some condition, make use of a 
``choose`` block. Inside it, you would declare a ``default`` element 
followed by one or more ``when`` elements. Each ``when`` element must
have a ``test`` attribute that contains a Python expression, which if 
``True``, its content will be used. If none of the ``when`` elements has 
a ``True`` expression, then the ``default`` element's content will be 
used. To enable debugging on workstation1, you might use::

  <config>
      <constants>
          <bool key="debug">
              <choose>
                  <default>False</default>
                  <when test="hostname == 'workstation1'">True</when>
              </choose>
          </bool>
      </constants>
  </config>

The *debug* constant will have a ``True`` value when evaluated on host
*workstation1* and ``False`` otherwise.

Please note that you cannot execute arbitrary Python code in a ``test``
attribute. You cannot import other Python modules, and the only local
variables (other than ``hostname``) are defined by your program in advance.

Importing
=========
Since usually many softwares are used together in an enterprise environment,
it makes sense to have the configuration for the software split into 
several pieces. This is advantageous for a few reasons. First, you might
have a few applications that are related and could benefit by importing the
configuration of one into the other. In other words, program *A* might 
benefit from sourcing the configuration for program *B* and using its
constants such as file locations, etc. In this case, you can organize your
configuration so that the constants that make the most sense for program 
*A* can go into its configuration document, and the ones that make the most
sense for program *B* can go in its configuration. Then, you can use all of
the configuration from both programs in each, without duplicating your work.

A second example might be that several different programs need to make use
of some common information, such as database connection strings or 
passwords. These common constants can be placed into a common configuration
document and be imported all the programs that need to make use of the
common data.

To import another document's constants, use the ``src`` attribute of the
``constants`` element to offer the location of the remote document::

  <config>
      <constants src="master.xml" />

      <!-- "Local" constants -->
      <constants>
          <string key="local">This is defined locally</string>
      </constants>
  </config>

In this example, the constants in the *master.xml* file will be imported
into this document and will be available to the program. The location of
the imported document is assumed to be relative to the path of the 
document importing it. In other words, we assume that ``master.xml`` is in
the same place as the file shown above.

Import Element Content
----------------------
You can also defer the contents of an element to a file as well. For 
instance, if you have a constant that contains javascript code to be
executed in your program, it will be difficult to embed that into an xml
file. First of all, your text editor probably won't highlight it properly,
and secondly, you cannot use xml symbols such as ``<`` or ``>`` unless 
you nest the element in some nasty ``<![CDATA[`` element, which definietly
doesn't make things look prettier. The best option is to have a separate
file named ``external_code.js`` and just import it into a ``string``
or similar::

    <string key="external_code" src="external_code.js" />

This will load the contents of the ``external_code.js`` file into your
configuration and be accessible via the ``external_code`` key.

Element content is cast to the type of the element given, so you don't
have to be limited to string content. For instance, if you have a file that
lists email addresses, one per line, you can import that as a list::

    <list key="distrubition" src="email_list.txt" delimiter="&#10;" />

The ``&#10;`` might be a bit cryptic, but in xml, it is difficult to
represent a standalone newline character. Technically, a newline character
is ASCII character number 10, so we can encode character #10 in a simple
xml entity as shown. Again, this assumes ``email_list.txt`` is in the
same path as the configuration document that sourced it. See the section
on relative paths (XXX) for more instructions.

References
==========
Now that you've imported some constants, you might want to base the 
values of your local constants on the ones imported. You might also want
to define a constant that is a root path and several constants that are
subfolders of this path::

  <config>
      <constants src="master.xml" />

      <constants>
          <string key="log_path">
              %(base_output_path)/log
          </string>
      </constants>
  </config>

In this example, it is assumed that the *master.xml* document defines a 
constant named ``base_output_path``. Locally we define a ``log_path``
constant that is the ``log`` subfolder of that path.

TODO: namespaces

Namespaces
==========
When importing other documents, many times we want to isolate the constants
from the foreign document so that we do not accidentally replace them with
constants defined in the local namespace. For this, we can specify a
namespace to contain the imported constants. This methodology can also be 
used to handle a circular dependency condition. If program *A* imports the
configuration of program *B* which imports the configuration of program *A*,
using namespaces can be used to easily separate the two configurations and
help keep track of documents already loaded.

To import the ``master.xml`` document into the *master* namespace, you might::

  <config>
      <constants namespace="master" src="master.xml" />

      <constants>
          <string key="log_path">
              %(master:base_output_path)/log
          </string>
      </constants>
  </config>

Here we give the namespace in the reference ``%(master:base_output_path)`` to
indicate that the ``base_output_path`` constant is declared in the *master*
namespace.

Environment Variables
---------------------
One namespace is both reserved and magical, *env*. Constants in the *env* 
namespace will resolve to their corresponding environment variables. You
cannot use this namespace to define or modify environment variables, so
don't attempt to import or create constants in the *env* namespace. To
use the value of an environment if it is defined and use a default 
otherwise, you could use::

    <!-- Temporary location. Prefer TMPDIR environment variable if set
         and default to /tmp otherwise -->
    <string key="TMPDIR">
        <choose>
            <when test="'%(env:TMPDIR)' != ''">%(env:TMPDIR)</string>
            <default>
                /tmp
            </default>
        </choose>
    </string>
