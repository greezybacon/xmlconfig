Configuration Interface
=======================
This is how you locate and load your configuration.

getConfig
---------
xmlconfig is designed similar to the Python logging module, so that 
configuration instances are created and registered through the ``getConfig``
function of the ``xmlconfig`` module. This allows configuration to be 
easily shared among multiple modules. To create and/or retrieve a XmlConfig 
instance, use the ``getConfig`` function::

    from xmlconfig import getConfig
    myConfig = getConfig()

``getConfig`` can receive a name used to represent its configuration 
contents. Subsequent calls to ``getConfig`` with the same name will return 
the same XmlConfig instance.

Loading
-------
Once you've obtained an XmlConfig instance, you need to load in a 
configuration document. You can utilize the ``load`` method for this. The
``load`` method receives a URL argument indicating where the configuration
document is located. Valid URLs are allowed to be any URL scheme that is 
registered in the Python ``urllib`` module. (``urllib2`` on Python 2.x).

Files
~~~~~
To load a configuration document as a file, you might use::

    myConfig.load("file:config/myconfig.xml")

This will load the ``myconfig.xml`` document located in the ``config``
subfolder of the current working path. If the folder ``config`` is not in
the current working path, you might use ``os.chdir`` to change the path, 
or use a relative (ie. with ``..``) or absolute location of the file. 

Since the file URL is likely the most common, you can quietly drop the
``file:`` part of the URL. In other words, this is equivalent to the above
example::

    myConfig.load("config/myconfig.xml")

Remote
~~~~~~
An alternative method might be to retrieve the configuration via a web
or ftp server. Since Python already supports this natively, you can easily
implement this::

    myConfig.load("https://github.com/greezybacon/xmlconfig/raw/master/test/config.xml")

More Complex
~~~~~~~~~~~~
**(Future)** You can pass a ``urllib.request.Request`` instance (``urllib2.Request`` 
for Python 2.x) into the ``load`` method instead of a string. This will be
useful if you need to specify an explicit proxy server, http basic 
authentication, special HTTP headers, etc. Ultimately, the value passed in 
is passed to the ``urlopen`` function. So if you can set things up and open
your document with a call to ``urlopen``, you could set things up and pass
the ``Request`` into the ``load`` method.

Automagic Loading
-----------------
The name you pass into ``getConfig`` can be used to automatically locate and
load in your configuration. For instance, you could also load the 
``myconfig.xml`` document this way::

    myConfig = getConfig("myconfig")
    myConfig.autoload()

By default, the ``autoload`` method will search for files named *name*.xml
in a folder named ``config`` in the current working path and up to three
parent folders. The *name* part of the file is the same as the *name* 
passed into the ``getConfig`` call. For instance, it will automatically find 
``../../config/myconfig.xml`` as well. The ``config`` folder part is also
completely optional and can be changed to another name if you like.

If your configuration document is a file accessible from the current 
working path, you won't need any extra arguments. However, if you need to
automagically load from an http server or such, you will need to provide
the base URL to begin searching::

    myConfig.autoload("http://my.website.ws/")

The remote URL will still be mangled to search for the config in the 
``config`` folder as well as in parent folders.

Interactive Automagicness
~~~~~~~~~~~~~~~~~~~~~~~~~~
**(Future)** In addition to automatically finding your configuration 
document, if more than one are found that match the pattern
*name*\*.xml, a dialog for GUI applications or a text menu for console
applications can be presented and allow the user to select the appropriate
configuration. This is useful, for instance, if your changing out
versions or your software or versions of another software that you interact
with. Being able to interactively select the configuration allows for
super simple fail-over and fail-back between configurations of your
software.

This will likely only be supported for the ``file:`` URLs.
