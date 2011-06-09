# vim: tabstop=4 shiftwidth=4 softtabstop=4

import boto
import mox

from boto.ec2.connection import EC2Connection
from django import test
from django_openstack.core import connection
from django_openstack.nova.manager import ProjectManager
from mox import And, ContainsKeyValue, IgnoreArg, In, IsA
from nova_adminclient import client as nova_client


TEST_IMAGE_ID = 1
TEST_INSTANCE_ID = 1
TEST_INSTANCE_IDS = range(8)
TEST_INSTANCE_NAME = 'testInstance'
TEST_PROJECT_NAME = 'testProject'
TEST_PROJECT_DESCRIPTION = 'testDescription'
TEST_PROJECT_MANAGER_ID = 100
TEST_PROJECT_MEMBER_IDS = []
TEST_REGION_ENDPOINT = 'http://testServer:8773/services/Cloud'
TEST_REGION_NAME = 'testRegion'
TEST_REGION = {'endpoint': TEST_REGION_ENDPOINT, 'name': TEST_REGION_NAME}
TEST_USER = 'testUser'


class ProjectManagerTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        project = nova_client.ProjectInfo()
        project.projectname = TEST_PROJECT_NAME
        project.projectManagerId = TEST_PROJECT_MANAGER_ID

        self.manager = ProjectManager(TEST_USER, project, TEST_REGION)

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_conn_mock(self, count=1):
        '''
        Stubs get_openstack_connection as an EC2Connection and returns the
        EC2Connection mock
        '''
        self.mox.StubOutWithMock(self.manager, 'get_openstack_connection')
        conn_mock = self.mox.CreateMock(EC2Connection)
        for i in range(count):
            self.manager.get_openstack_connection().AndReturn(conn_mock)
        return conn_mock

    def test_get_openstack_connection(self):
        self.mox.StubOutWithMock(connection, 'get_nova_admin_connection')
        admin_mock = self.mox.CreateMock(nova_client.NovaAdminClient)
        admin_mock.connection_for(TEST_USER, TEST_PROJECT_NAME,
                                  clc_url=TEST_REGION_ENDPOINT,
                                  region=TEST_REGION_NAME)
        connection.get_nova_admin_connection().AndReturn(admin_mock)

        self.mox.ReplayAll()

        self.manager.get_openstack_connection()

        self.mox.VerifyAll()

    def test_get_zip(self):
        self.mox.StubOutWithMock(connection, 'get_nova_admin_connection')
        admin_mock = self.mox.CreateMock(nova_client.NovaAdminClient)
        admin_mock.get_zip(TEST_USER, TEST_PROJECT_NAME)
        connection.get_nova_admin_connection().AndReturn(admin_mock)

        self.mox.ReplayAll()

        self.manager.get_zip()

        self.mox.VerifyAll()

    def test_get_images(self):
        ''' TODO: Need to figure out what I'm doing here...'''
        self.assertTrue(False)
        TEST_IMAGE_IDS = [TEST_IMAGE_ID, TEST_IMAGE_ID + 1]
        self.mox.StubOutwithMock(self.manager, 'get_openstack_connection')
        conn_mock = self.mox.CreateMock(EC2Connection)
        images_mock = self.mox.CreateMockAnything()

    def test_get_image(self):
        TEST_IMAGE_BAD_ID = TEST_IMAGE_ID + 1
        self.mox.StubOutWithMock(self.manager, 'get_images')
        self.manager.get_images(image_ids=[TEST_IMAGE_ID]).AndReturn(
                [TEST_IMAGE_ID])
        self.manager.get_images(image_ids=[TEST_IMAGE_BAD_ID]).AndReturn([])

        self.mox.ReplayAll()

        image_result = self.manager.get_image(TEST_IMAGE_ID)
        self.assertEqual(TEST_IMAGE_ID, image_result)

        image_result = self.manager.get_image(TEST_IMAGE_BAD_ID)
        self.assertTrue(image_result is None)

        self.mox.VerifyAll()

    def test_deregister_image(self):
        conn_mock = self.stub_conn_mock()
        conn_mock.deregister_image(TEST_IMAGE_ID).AndReturn(TEST_IMAGE_ID)

        self.mox.ReplayAll()

        deregistered_id = self.manager.deregister_image(TEST_IMAGE_ID)

        self.assertEqual(deregistered_id, TEST_IMAGE_ID)

        self.mox.VerifyAll()

    def test_update_image(self):
        TEST_DISPLAY_NAME = 'testDisplayName'
        TEST_DESCRIPTION = 'testDescription'
        TEST_RETURN = 'testReturnString'

        conn_mock = self.stub_conn_mock(count=2)

        conn_mock.get_object('UpdateImage', And(
                             ContainsKeyValue('ImageId', TEST_IMAGE_ID),
                             ContainsKeyValue('DisplayName', TEST_DISPLAY_NAME),
                             ContainsKeyValue('Description', TEST_DESCRIPTION)
                             ),
                             boto.ec2.image.Image).AndReturn(TEST_RETURN)
        conn_mock.get_object('UpdateImage', And(
                             ContainsKeyValue('ImageId', TEST_IMAGE_ID),
                             ContainsKeyValue('DisplayName', None),
                             ContainsKeyValue('Description', None)
                             ),
                             boto.ec2.image.Image).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        update_result = self.manager.update_image(TEST_IMAGE_ID,
                                  display_name=TEST_DISPLAY_NAME,
                                  description=TEST_DESCRIPTION)

        self.assertEqual(update_result, TEST_RETURN)

        update_result = self.manager.update_image(TEST_IMAGE_ID)

        self.assertEqual(update_result, TEST_RETURN)

        self.mox.VerifyAll()

    def test_modify_image_attribute(self):
        TEST_RETURN = 'testReturnValue'
        TEST_ATTRIBUTE = 'testAttribute'
        TEST_OPERATION = 'testOperation'
        TEST_GROUPS = 'testGroups'

        conn_mock = self.stub_conn_mock(count=2)

        # Test: default attributes passed
        conn_mock.modify_image_attribute(TEST_IMAGE_ID,
                                         attribute=None,
                                         operation=None,
                                         groups='all').AndReturn(TEST_RETURN)
        # Test: custom attributes passed
        conn_mock.modify_image_attribute(TEST_IMAGE_ID,
                                         attribute=TEST_ATTRIBUTE,
                                         operation=TEST_OPERATION,
                                         groups=TEST_GROUPS
                                        ).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        modify_return = self.manager.modify_image_attribute(TEST_IMAGE_ID)
        self.assertEqual(modify_return, TEST_RETURN)

        modify_return = \
                self.manager.modify_image_attribute(TEST_IMAGE_ID,
                                                    attribute=TEST_ATTRIBUTE,
                                                    operation=TEST_OPERATION,
                                                    groups=TEST_GROUPS)
        self.assertEqual(modify_return, TEST_RETURN)

        self.mox.VerifyAll()

    def test_run_instances(self):
        TEST_RETURN = 'testReturnValue'

        conn_mock = self.stub_conn_mock()

        conn_mock.run_instances(TEST_IMAGE_ID,
                                key_name='testKey',
                                user_data='userData').AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        run_return = self.manager.run_instances(TEST_IMAGE_ID,
                                                key_name='testKey',
                                                user_data='userData')
        self.assertEqual(run_return, TEST_RETURN)

        self.mox.VerifyAll()

    def test_get_instance_count(self):
        self.mox.StubOutWithMock(self.manager, 'get_instances')

        def valid_instance_list():
            self.manager.get_instances().AndReturn(TEST_INSTANCE_IDS)
            self.mox.ReplayAll()
            self.assertEqual(len(TEST_INSTANCE_IDS),
                             self.manager.get_instance_count())
            self.mox.VerifyAll()
            self.mox.ResetAll()

        def invalid_instance_list():
            self.manager.get_instances().AndReturn(None)
            self.mox.ReplayAll()
            self.assertTrue(self.manager.get_instance_count() is None)
            self.mox.VerifyAll()
            self.mox.ResetAll()

        valid_instance_list()
        invalid_instance_list()

    def get_reservation_mock(self, instance_ids):
        rMock = self.mox.CreateMock(boto.ec2.instance.Reservation)
        instances = []
        for instance_id in instance_ids:
            instance = boto.ec2.instance.Instance()
            instance.id = instance_id
            instances.append(instance)
        rMock.instances = instances

        return rMock

    def get_single_instance_single_reservation(self, instance_id):
        return self.get_reservation_mock([instance_id])

    def get_multiple_instances_multiple_reservations(self, instance_ids):
        rMock1 = \
            self.get_reservation_mock(instance_ids[:len(instance_ids) // 2])
        rMock2 = \
            self.get_reservation_mock(instance_ids[len(instance_ids) // 2:])
        return [rMock1, rMock2]

    def test_get_instances(self):

        def single_instance_single_reservation():
            conn_mock = self.stub_conn_mock()
            rMock = \
                self.get_single_instance_single_reservation(TEST_INSTANCE_ID)
            conn_mock.get_all_instances().AndReturn([rMock])

            self.mox.ReplayAll()

            instances = self.manager.get_instances()
            self.assertEqual(1, len(instances))
            self.assertEqual(TEST_INSTANCE_ID, instances[0].id)

            self.mox.VerifyAll()
            self.mox.ResetAll()

        def multiple_instances_multiple_reservations():
            conn_mock = self.stub_conn_mock()
            rMocks = self.get_multiple_instances_multiple_reservations(
                        TEST_INSTANCE_IDS)

            conn_mock.get_all_instances().AndReturn(rMocks)

            self.mox.ReplayAll()

            instances = self.manager.get_instances()
            self.assertEqual(len(TEST_INSTANCE_IDS), len(instances))
            instance_ids = [instance.id for instance in instances]
            # Upgrade to 2.7 to make this work
            # self.assertItemsEqual(instance_ids, TEST_INSTANCE_IDS)
            for instance_id in instance_ids:
                self.assertTrue(instance_id in TEST_INSTANCE_IDS)

            self.mox.VerifyAll()
            self.mox.ResetAll()

        single_instance_single_reservation()
        multiple_instances_multiple_reservations()

    def test_get_instance(self):

        def single_instance_single_reservation():
            conn_mock = self.stub_conn_mock()
            rMock = \
                self.get_single_instance_single_reservation(TEST_INSTANCE_ID)
            conn_mock.get_all_instances().AndReturn([rMock])

            self.mox.ReplayAll()

            instance = self.manager.get_instance(TEST_INSTANCE_ID)
            self.assertEqual(instance.id, TEST_INSTANCE_ID)

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def multiple_instances_multiple_reservations():
            INDEX = 4
            conn_mock = self.stub_conn_mock()
            rMocks = self.get_multiple_instances_multiple_reservations(
                        TEST_INSTANCE_IDS)
            conn_mock.get_all_instances().AndReturn(rMocks)

            self.mox.ReplayAll()

            instance = self.manager.get_instance(TEST_INSTANCE_IDS[INDEX])
            self.assertEqual(instance.id, TEST_INSTANCE_IDS[INDEX])

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def instance_missing():
            conn_mock = self.stub_conn_mock()
            rMock = \
                self.get_single_instance_single_reservation(TEST_INSTANCE_ID)
            conn_mock.get_all_instances().AndReturn([rMock])

            self.mox.ReplayAll()

            instance = self.manager.get_instance(TEST_INSTANCE_ID + 1)
            self.assertTrue(instance is None)

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        single_instance_single_reservation()
        multiple_instances_multiple_reservations()
        instance_missing()

    def test_update_instance(self):
        TEST_DESCRIPTION = 'testDescription'
        TEST_RETURN = 'returnValue'
        conn_mock = self.stub_conn_mock()
        conn_mock.get_object('UpdateInstance', And(
                             ContainsKeyValue('InstanceId',
                                              TEST_INSTANCE_ID),
                             ContainsKeyValue('DisplayName',
                                              TEST_INSTANCE_NAME),
                             ContainsKeyValue('DisplayDescription',
                                              TEST_DESCRIPTION),
                             ),
                boto.ec2.instance.Instance).AndReturn(TEST_RETURN)

        updates = {'nickname': TEST_INSTANCE_NAME,
                   'description': TEST_DESCRIPTION}

        self.mox.ReplayAll()

        retVal = self.manager.update_instance(TEST_INSTANCE_ID, updates)
        self.assertEqual(retVal, TEST_RETURN)

        self.mox.VerifyAll()

    def test_get_instance_graph(self):
        self.assertTrue(False)

    def test_terminate_instance(self):
        conn_mock = self.stub_conn_mock()
        conn_mock.terminate_instances([TEST_INSTANCE_ID])

        self.mox.ReplayAll()

        self.manager.terminate_instance(TEST_INSTANCE_ID)

        self.mox.VerifyAll()

    def test_get_security_groups(self):
        TEST_SECURITY_GROUPS=['group1', 'group2']

        conn_mock = self.stub_conn_mock()
        conn_mock.get_all_security_groups().AndReturn(TEST_SECURITY_GROUPS)

        self.mox.ReplayAll()
        
        groups = self.manager.get_security_groups()
        # Upgrade to 2.7 to make this work
        # self.assertItemsEqual(groups, TEST_SECURITY_GROUPS)
        for group in groups:
             self.assertTrue(group in TEST_SECURITY_GROUPS)

    def test_get_security_group(self):
        TEST_SECURITY_GROUP_NAME = 'group1'
        TEST_RETURN = 'returnValue'
        conn_mock = self.stub_conn_mock(count=2)
        conn_mock.get_all_security_groups(
                groupnames=TEST_SECURITY_GROUP_NAME.encode('ascii')
                ).AndReturn([TEST_RETURN])
        conn_mock.get_all_security_groups(
                groupnames=TEST_SECURITY_GROUP_NAME.encode('ascii')
                ).AndReturn([])

        self.mox.ReplayAll()

        # Something is there
        group = self.manager.get_security_group(TEST_SECURITY_GROUP_NAME)
        self.assertEqual(group, TEST_RETURN)

        # Nothing is there
        group = self.manager.get_security_group(TEST_SECURITY_GROUP_NAME)
        self.assertEqual(group, None)

        self.mox.VerifyAll()

    def test_has_security_group(self):
        pass

    def test_create_security_group(self):
        pass

    def test_delete_security_group(self):
        pass

    def test_authorize_security_group(self):
        pass

    def test_revoke_security_group(self):
        pass

    def test_get_key_pairs(self):
        pass

    def test_get_key_pair(self):
        pass

    def test_has_key_pair(self):
        pass

    def test_create_key_pair(self):
        pass

    def test_delete_key_pair(self):
        pass

    def test_get_volumes(self):
        pass

    def test_create_volume(self):
        pass

    def test_delete_volume(self):
        pass

    def test_attach_volume(self):
        pass

    def test_detach_volume(self):
        pass