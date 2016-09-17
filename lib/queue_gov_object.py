import pdb
from pprint import pprint
import os
import sys
sys.path.append( os.path.join( os.path.dirname(__file__), '..', 'lib' ) )
import models
from bitcoinrpc.authproxy import JSONRPCException
import misc
import re

# mixin for GovObj composed classes like proposal and superblock, etc.
class GovernanceClass(object):
    # lazy
    @property
    def go(self):
        return self.governance_object

    def vote(self, dashd, signal, outcome):
        return self.go.vote(dashd, signal, outcome)

    def voted_on(self, **kwargs):
        return self.go.voted_on(**kwargs)

    def vote_validity(self, dashd):
        if self.is_valid(dashd):
            print "Voting valid! %s: %d" % (self.__class__.__name__, self.id)
            self.vote(dashd, 'valid', 'yes')
        else:
            print "Voting INVALID! %s: %d" % (self.__class__.__name__, self.id)
            self.vote(dashd, 'valid', 'no')

    def list(self):
        dikt = {
            "Name": self.name,
            "DataHex": self.governance_object.object_data,
            "Hash": self.object_hash,
            "CollateralHash": self.governance_object.object_fee_tx,
            "AbsoluteYesCount": self.governance_object.absolute_yes_count,
            "YesCount": self.governance_object.yes_count,
            "NoCount": self.governance_object.no_count,
            "AbstainCount": self.governance_object.abstain_count,
        }

        # return a dict similar to dashd "gobject list" output
        return { self.name: dikt }

    # boolean -- does the object meet collateral confirmations?
    def submit(self, dashd):
        go = self.governance_object

        # don't attempt to submit a superblock unless a masternode
        # note: will probably re-factor this, this has code smell
        my_vin = dashd.get_current_masternode_vin()
        if (isinstance(self, models.Superblock) and (my_vin == None)):
            print "Not a masternode. Only masternodes may submit superblocks."
            return

        print " -- submit cmd : ", ' '.join(self.get_submit_command())
        print
        print " -- executing submit ... getting object hash"
        object_hash = dashd.rpc_command(*self.get_submit_command())
        print " -- got hash: [%s]" % object_hash

        go.object_hash = object_hash
        go.save()

    def serialise(self):
        import inflection
        import binascii
        import simplejson

        # 'proposal', 'superblock', etc.
        name = self._meta.name
        obj_type = inflection.singularize(name)

        return binascii.hexlify(simplejson.dumps( (obj_type, self.get_dict()) , sort_keys = True))

    def dashd_serialise(self):
        import dashlib
        return dashlib.SHIM_serialise_for_dashd(self.serialise())

    @classmethod
    def serialisable_fields(self):
        # Python is so not very elegant...
        pk_column  = self._meta.primary_key.db_column
        fk_columns = [ fk.db_column for fk in self._meta.rel.values() ]
        do_not_use = [ pk_column ]
        do_not_use.extend(fk_columns)
        do_not_use.append('object_hash')
        fields_to_serialise = self._meta.columns.keys()

        for field in do_not_use:
            if field in fields_to_serialise:
                fields_to_serialise.remove(field)

        return fields_to_serialise

    def get_dict(self):
        dikt = {}

        for field_name in self.serialisable_fields():
            dikt[ field_name ] = getattr( self, field_name )

        return dikt
