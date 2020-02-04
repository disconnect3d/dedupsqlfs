# -*- coding: utf8 -*-

__author__ = 'sergey'

from sqlite3 import Binary
from dedupsqlfs.db.sqlite.table import Table

class TableHash( Table ):

    _table_name = "hash"

    def create( self ):
        c = self.getCursor()

        # Create table
        c.execute(
            "CREATE TABLE IF NOT EXISTS `%s` (" % self.getName()+
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "+
                "hash BINARY(64) NOT NULL"+
            ")"
        )
        self.createIndexIfNotExists('hash', ('hash',), True)
        return

    def insert( self, value):
        self.startTimer()
        cur = self.getCursor()
        bvalue = Binary(value)
        cur.execute("INSERT INTO `%s`(hash) VALUES (?)" % self.getName(),
                    (bvalue,))
        item = cur.lastrowid
        self.stopTimer('insert')
        return item

    def insertRaw( self, rowId, value):
        self.startTimer()
        cur = self.getCursor()
        bvalue = Binary(value)
        cur.execute("INSERT INTO `%s`(id,hash) VALUES (?,?)" % self.getName(),
                    (rowId,bvalue,))
        item = cur.lastrowid
        self.stopTimer('insertRaw')
        return item

    def update( self, item_id, value ):
        """
        @return: count updated rows
        @rtype: int
        """
        self.startTimer()
        cur = self.getCursor()
        bvalue = Binary(value)
        cur.execute("UPDATE `%s` SET hash=? WHERE id=?" % self.getName(),
                    (bvalue, item_id))
        count = cur.rowcount
        self.stopTimer('update')
        return count

    def get( self, item_id ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT hash FROM `%s` WHERE id=?" % self.getName(), (item_id,))
        item = cur.fetchone()
        if item:
            item = item["hash"]
        self.stopTimer('get')
        return item

    def find( self, value ):
        self.startTimer()
        cur = self.getCursor()
        bvalue = Binary(value)
        cur.execute("SELECT id FROM `%s` WHERE hash=?" % self.getName(), (bvalue,))
        item = cur.fetchone()
        if item:
            item = item["id"]
        self.stopTimer('find')
        return item

    def get_count(self):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT COUNT(1) as `cnt` FROM `%s`" % self.getName())
        item = cur.fetchone()
        if item:
            item = item["cnt"]
        else:
            item = 0
        self.stopTimer('get_count')
        return item

    def get_hash_ids(self, start_id, end_id):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT `id` FROM `%s` " % self.getName()+
                    " WHERE `id`>=? AND `id`<?", (start_id, end_id,))
        nameIds = set(item["id"] for item in iter(cur.fetchone, None))
        self.stopTimer('get_hash_ids')
        return nameIds

    def remove_by_ids(self, id_str):
        self.startTimer()
        count = 0
        if id_str:
            cur = self.getCursor()
            cur.execute("DELETE FROM `%s` " % self.getName()+
                        " WHERE `id` IN (%s)" % (id_str,))
            count = cur.rowcount
        self.stopTimer('remove_by_ids')
        return count

    pass
