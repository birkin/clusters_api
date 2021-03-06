# -*- coding: utf-8 -*-

""" Grabs html, parses, and saves json to disk. """

from __future__ import unicode_literals
import datetime, json, pprint, sys
import requests
from bs4 import BeautifulSoup
from clusters_api.config import settings
# from clusters_api.utils import logger_setup


class Grabber(object):
    """ TODO: once server acls are set up, re-enable logging. """

    def __init__( self ):
        """ Sets up basics. """
        self.parser = None
        self.parser = Parser()

    # def __init__( self, log ):
    #     """ Sets up basics. """
    #     self.log = log
    #     self.parser = None
    #     self.parser = Parser( self.log )

    def update_data( self ):
        """ Accesses source html, parses it, and saves json to disk. """
        r = requests.get( settings.SOURCE_URL )
        html = r.content.decode( 'utf-8' )
        clusters_dict = self.parser.parse_cluster_html( html )
        save_dict = {
            'datetime_updated': unicode( datetime.datetime.now() ),
            'counts': clusters_dict }
        jstring = json.dumps( save_dict, sort_keys=True, indent=2 )
        with open( settings.JSON_FILE_PATH, 'w' ) as f:
            f.write( jstring )
        return


class Parser(object):

    def __init__( self ):
       """ Sets up basics. """
       self.cluster_name_mapper = {  # source-html-name: api-name
            'Rock 1st Floor': 'rock-level-1',
            'Rock 2nd Floor': 'rock-level-2-main',
            'Rock Grad': 'rock-level-2-grad',
            'Friedman': 'scili-friedman',
            'SciLi Mezz': 'scili-mezzanine' }

    # def __init__( self, log ):
    #    """ Sets up basics. """
    #    self.log = log
    #    self.cluster_name_mapper = {  # source-html-name: api-name
    #         'Rock 1st Floor': 'rock-level-1',
    #         'Rock 2nd Floor': 'rock-level-2-main',
    #         'Rock Grad': 'rock-level-2-grad',
    #         'Friedman': 'scili-friedman',
    #         'SciLi Mezz': 'scili-mezzanine' }

    def parse_cluster_html( self, html ):
        """ Takes source html.
            Parses out cluster data.
            Returns dict.
            Note: this used the mobile site, which doesn't directly contain all the info needed. """
        table_rows = self._grab_cluster_tablerows( html )
        data_dict = {}
        for row in table_rows:
          title = self._extract_title( row )
          if title in self.cluster_name_mapper.keys():
            count_dict = self._extract_counts( row )
            data_dict[ self.cluster_name_mapper[title] ] = count_dict  # takes, eg, title 'Rock 1st Floor' and stores key as 'rock-level-1'
        api_data_dict = self._tweak_counts( data_dict )
        return api_data_dict

    def _grab_cluster_tablerows( self, html ):
        """ Helper. Grabs cluster table-row objects from html.
            Returns list of BeautifulSoup dom objects. """
        soup = BeautifulSoup( html )
        table_rows = soup.findAll( 'tr' )
        relevant_tablerows = []
        for row in table_rows:
            table_cells = row.findAll( 'td' )
            if len( table_cells ) == 9:
                relevant_tablerows.append( row )
        return relevant_tablerows

    def _extract_title( self, row ):
        """ Helper. Grabs title from table-row object.
            Returns unicode-string or None. """
        title_cell = row.findAll( 'td' )[0]
        a_link = title_cell.findAll( 'a' )
        title = None
        if len( a_link ) > 0:  # goal: '''[<a href="javascript:loadPieChart(11)">Rock 1st Floor</a>]'''
            title = unicode( a_link[0].string )
        return title

    def _extract_counts( self, row ):
        """ Helper. Grabs count info from table-row object.
            Returns dict; counts are integers. """
        table_cells = row.findAll( 'td' )
        rawdata_count_names = [ 'In Use', 'Available Stations', 'Unavailable Stations', 'Offline Stations', 'Total Stations' ]  # don't re-order; this is order in rawdata
        count_dict = {}; i = 0
        for cell in table_cells:
            try:
               count = int( cell.string )
               count_dict[ rawdata_count_names[i] ] = count
               i += 1
            except:
              pass
        return count_dict

    def _tweak_counts( self, data_dict ):
        """ Helper. Updates count_dict labels to api-compatible ones; adds useful 'calculated_available' data.
            Returns dict. """
        updated_data_dict = {}
        for key, value in data_dict.items():
            cluster_name = key; count_dict = value
            updated_count_dict = {
                'available': count_dict['Available Stations'],
                'calculated_available': count_dict['Available Stations'] + count_dict['Offline Stations'],
                'in_use': count_dict['In Use'],
                'offline': count_dict['Offline Stations'],
                'total': count_dict['Total Stations'] }
            updated_data_dict[cluster_name] = updated_count_dict
        return updated_data_dict



if __name__ == '__main__':
    """ Assumes env is activated.
        Called by cron script.
        TODO: once server acls are set up, re-enable logging. """
    try:
        grabber = Grabber()
        grabber.update_data()
    except Exception as e:
        message = '- in grabber_handler.__main__; exception updating data, %s' % unicode(repr(e))
        print message

# if __name__ == '__main__':
#     """ Assumes env is activated.
#         Called by cron script. """
#     try:
#         log = logger_setup.setup_logger()
#     except Exception as e:
#         print '- in grabber_handler.__main__; exception setting up logger, %s' % unicode(repr(e))
#         sys.exit()
#     try:
#         grabber = Grabber( log )
#         grabber.update_data()
#     except Exception as e:
#         message = '- in grabber_handler.__main__; exception updating data, %s' % unicode(repr(e))
#         print message
#         log.error( message )
