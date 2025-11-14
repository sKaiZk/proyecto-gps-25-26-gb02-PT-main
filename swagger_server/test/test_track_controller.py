# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.track import Track  # noqa: E501
from swagger_server.test import BaseTestCase


class TestTrackController(BaseTestCase):
    """TrackController integration test stubs"""

    def test_add_track(self):
        """Test case for add_track

        Add a new track to the database
        """
        body = Track()
        response = self.client.open(
            '/track/upload',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_track(self):
        """Test case for delete_track

        Deletes a track.
        """
        response = self.client.open(
            '/track/{trackId}'.format(track_id=789),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_track(self):
        """Test case for get_track

        Gets a track info by Id
        """
        response = self.client.open(
            '/track/{trackId}'.format(track_id=789),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_track(self):
        """Test case for update_track

        Updates a track from the database with form data.
        """
        body = Track()
        response = self.client.open(
            '/track/{trackId}'.format(track_id=789),
            method='PATCH',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
