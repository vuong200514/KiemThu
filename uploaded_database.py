"""
This module contains the main component of TinyDB: the database.
"""

from collections .abc import Iterator 

from .import JSONStorage 
from .storages import Storage 
from .table import Table ,Document 
from .utils import with_typehint 



TableBase :type [Table ]=with_typehint (Table )




# Tóm tắt: lớp
class TinyDB (TableBase ):
    """
    The main class of TinyDB.

    The ``TinyDB`` class is responsible for creating the storage class instance
    that will store this database's documents, managing the database
    tables as well as providing access to the default table.

    For table management, a simple ``dict`` is used that stores the table class
    instances accessible using their table name.

    Default table access is provided by forwarding all unknown method calls
    and property access operations to the default table by implementing
    ``__getattr__``.

    When creating a new instance, all arguments and keyword arguments (except
    for ``storage``) will be passed to the storage class that is provided. If
    no storage class is specified, :class:`~tinydb.storages.JSONStorage` will be
    used.

    .. admonition:: Customization

        For customization, the following class variables can be set:

        - ``table_class`` defines the class that is used to create tables,
        - ``default_table_name`` defines the name of the default table, and
        - ``default_storage_class`` will define the class that will be used to
          create storage instances if no other storage is passed.

        .. versionadded:: 4.0

    .. admonition:: Data Storage Model

        Data is stored using a storage class that provides persistence for a
        ``dict`` instance. This ``dict`` contains all tables and their data.
        The data is modelled like this::

            {
                'table1': {
                    0: {document...},
                    1: {document...},
                },
                'table2': {
                    ...
                }
            }

        Each entry in this ``dict`` uses the table name as its key and a
        ``dict`` of documents as its value. The document ``dict`` contains
        document IDs as keys and the documents themselves as values.

    :param storage: The class of the storage to use. Will be initialized
                    with ``args`` and ``kwargs``.
    """




    table_class =Table 




    default_table_name ='_default'




    default_storage_class =JSONStorage 



# Tóm tắt: Create a new instance of TinyDB.
    def __init__ (self ,*args ,**kwargs )->None :
        """
        Create a new instance of TinyDB.
        """

        storage =kwargs .pop ('storage',self .default_storage_class )


        self ._storage :Storage =storage (*args ,**kwargs )

        self ._opened =True 
        self ._tables :dict [str ,Table ]={}



# Tóm tắt: Không có docstring cho __repr__
    def __repr__ (self ):

        args =[
        f'tables={list(self.tables())}',
        f'tables_count={len(self.tables())}',
        f'default_table_documents_count={self.__len__()}',
        f'all_tables_documents_count={[f"{table}={len(self.table(table))}" for table in self.tables()]}',
        ]

        return '<{} {}>'.format (type (self ).__name__ ,', '.join (args ))



# Tóm tắt: bảng
    def table (self ,name :str ,**kwargs )->Table :
        """
        Get access to a specific table.

        If the table hasn't been accessed yet, a new table instance will be
        created using the :attr:`~tinydb.database.TinyDB.table_class` class.
        Otherwise, the previously created table instance will be returned.

        All further options besides the name are passed to the table class which
        by default is :class:`~tinydb.table.Table`. Check its documentation
        for further parameters you can pass.

        :param name: The name of the table.
        :param kwargs: Keyword arguments to pass to the table class constructor
        """

        if name in self ._tables :
            return self ._tables [name ]

        table =self .table_class (self .storage ,name ,**kwargs )
        self ._tables [name ]=table 

        return table 



# Tóm tắt: bảng
    def tables (self )->set [str ]:
        """
        Get the names of all tables in the database.

        :returns: a set of table names
        """




















        return set (self .storage .read ()or {})



# Tóm tắt: bảng
    def drop_tables (self )->None :
        """
        Drop all tables from the database. **CANNOT BE REVERSED!**
        """



        self .storage .write ({})



        self ._tables .clear ()



# Tóm tắt: bảng
    def drop_table (self ,name :str )->None :
        """
        Drop a specific table from the database. **CANNOT BE REVERSED!**

        :param name: The name of the table to drop.
        """



        if name in self ._tables :
            del self ._tables [name ]

        data =self .storage .read ()


        if data is None :
            return 


        if name not in data :
            return 


        del data [name ]


        self .storage .write (data )



# Tóm tắt: lưu trữ
    @property 
    def storage (self )->Storage :
        """
        Get the storage instance used for this TinyDB instance.

        :return: This instance's storage
        :rtype: Storage
        """
        return self ._storage 



# Tóm tắt: đóng
    def close (self )->None :
        """
        Close the database.

        This may be needed if the storage instance used for this database
        needs to perform cleanup operations like closing file handles.

        To ensure this method is called, the TinyDB instance can be used as a
        context manager::

            with TinyDB('data.json') as db:
                db.insert({'foo': 'bar'})

        Upon leaving this context, the ``close`` method will be called.
        """
        self ._opened =False 
        self .storage .close ()



# Tóm tắt: Use the database as a context manager.
    def __enter__ (self ):
        """
        Use the database as a context manager.

        Using the database as a context manager ensures that the
        :meth:`~tinydb.database.TinyDB.close` method is called upon leaving
        the context.

        :return: The current instance
        """
        return self 



# Tóm tắt: lưu trữ
    def __exit__ (self ,*args ):
        """
        Close the storage instance when leaving a context.
        """
        if self ._opened :
            self .close ()



# Tóm tắt: bảng
    def __getattr__ (self ,name ):
        """
        Forward all unknown attribute calls to the default table instance.
        """
        return getattr (self .table (self .default_table_name ),name )






# Tóm tắt: bảng
    def __len__ (self ):
        """
        Get the total number of documents in the default table.

        >>> db = TinyDB('db.json')
        >>> len(db)
        0
        """
        return len (self .table (self .default_table_name ))



# Tóm tắt: bảng
    def __iter__ (self )->Iterator [Document ]:
        """
        Return an iterator for the default table's documents.
        """
        return iter (self .table (self .default_table_name ))
