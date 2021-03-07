from Tests.user.base_user import UserBaseTestCase

from flask import url_for


class ManageUserTestCase(UserBaseTestCase):
    def assert_details_equal(self, params):
        self.assertEqual(self.cA.first_name, params['first_name'])
        self.assertEqual(self.cA.last_name, params['last_name'])
        self.assertEqual(self.cA.username, params['username'])
        self.assertEqual(self.cA.email, params['email'])

    def assert_details_not_equal(self, params):
        self.assertNotEqual(params['first_name'], self.cA.first_name)
        self.assertNotEqual(params['last_name'], self.cA.last_name)
        self.assertNotEqual(params['username'], self.cA.username)
        self.assertNotEqual(params['email'], self.cA.email)

    def test_manage_user_loads(self):
        with self.client:
            self.login_customerA()
            res = self.client.get(url_for('user.manage'))

            self.assert200(res)
            self.assertIn(b'Update Details', res.data)
            self.assertIn(b'Change Password', res.data)

            # Ensure shown details are correct
            self.assertIn(self.cA.first_name.encode(), res.data)
            self.assertIn(self.cA.last_name.encode(), res.data)
            self.assertIn(self.cA.username.encode(), res.data)
            self.assertIn(self.cA.email.encode(), res.data)

    # Update details
    def test_change_user_details_correct_same(self):
        with self.client:
            self.login_customerA()
            params = dict(
                first_name=self.cA.first_name,
                last_name=self.cA.last_name,
                username=self.cA.username,
                email=self.cA.email,
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.update_user_details'), data=params)
            self.assert200(res)

            self.assert_details_equal(params)
            self.assertEqual(self.cA.confirmed, True)

    def test_change_user_details_correct_same_not_confirmed(self):
        with self.client:
            self.cA.confirmed = False

            self.login_customerA()
            params = dict(
                first_name=self.cA.first_name,
                last_name=self.cA.last_name,
                username=self.cA.username,
                email=self.cA.email,
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.update_user_details'), data=params)
            self.assert200(res)

            self.assert_details_equal(params)
            self.assertEqual(self.cA.confirmed, False)

    def test_change_user_details_correct_changed(self):
        with self.client:
            self.login_customerA()
            params = dict(
                first_name='new first name',
                last_name='new last name',
                username='new username',
                email='new.email@example.com',
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.update_user_details'), data=params)
            self.assert200(res)

            self.assert_details_equal(params)
            self.assertEqual(self.cA.confirmed, False)

    def test_change_user_details_invalid(self):
        with self.client:
            self.login_customerA()
            params = dict(
                first_name='f',
                last_name='f',
                username='new realllllllly long username',
                email='not an email',
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.update_user_details'), data=params)
            self.assert400(res)

            self.assertIn(b'Field must be between 2 and 20 characters long.', res.data)
            self.assertIn(b'Invalid email address.', res.data)

            self.assert_details_not_equal(params)
            self.assertEqual(self.cA.confirmed, True)

    def test_change_user_details_duplicate(self):
        with self.client:
            self.login_customerA()
            params = dict(
                first_name=self.cA.first_name,
                last_name=self.cA.last_name,
                username=self.cB.username,
                email=self.cB.email,
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.update_user_details'), data=params)
            self.assert400(res)

            self.assertIn(b'Username already registered to an account.', res.data)
            self.assertIn(b'Email already registered to an account.', res.data)

            self.assertEqual(params['first_name'], self.cA.first_name)
            self.assertEqual(params['last_name'], self.cA.last_name)
            self.assertNotEqual(params['username'], self.cA.username)
            self.assertNotEqual(params['email'], self.cA.email)
            self.assertEqual(self.cA.confirmed, True)

    def test_change_user_details_no_csrf(self):
        with self.client:
            self.login_customerA()
            params = dict(
                first_name='new first name',
                last_name='new last name',
                username='new username',
                email='new.email@example.com'
            )
            res = self.client.post(url_for('user.update_user_details'), data=params)
            self.assert400(res)

            self.assert_details_not_equal(params)
            self.assertEqual(self.cA.confirmed, True)

    # Change password
    def test_user_change_password_correct_same(self):
        with self.client:
            self.login_customerA()

            params = dict(
                current_password=self.cA.plain_test_password,
                password=self.cA.plain_test_password,
                password_confirm=self.cA.plain_test_password,
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.change_password'), data=params)
            self.assert200(res)

            # Ensure password was changed (new salt)
            self.assertTrue(self.cA.check_password(self.cA.plain_test_password))

    def test_user_change_password_correct(self):
        with self.client:
            self.login_customerA()
            new_password = 'new password 123'

            params = dict(
                current_password=self.cA.plain_test_password,
                password=new_password,
                password_confirm=new_password,
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.change_password'), data=params)
            self.assert200(res)

            # Ensure password was changed
            self.assertTrue(self.cA.check_password(new_password))

    def test_user_change_password_incorrect_password(self):
        with self.client:
            self.login_customerA()
            new_password = 'new password 123'

            params = dict(
                current_password='not the current password',
                password=new_password,
                password_confirm=new_password,
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.change_password'), data=params)
            self.assert400(res)

            # Ensure password was not changed
            self.assertTrue(self.cA.check_password(self.cA.plain_test_password))

    def test_user_change_password_invalid_form(self):
        with self.client:
            self.login_customerA()

            params = dict(
                current_password=self.cA.plain_test_password,
                password='a new password',
                password_confirm='not the same new password',
                csrf_token=self.csrf_token
            )
            res = self.client.post(url_for('user.change_password'), data=params)
            self.assert400(res)

            # Ensure password was not changed
            self.assertTrue(self.cA.check_password(self.cA.plain_test_password))

    def test_user_change_password_no_csrf(self):
        with self.client:
            self.login_customerA()
            new_password = 'new password 123'

            params = dict(
                current_password=self.cA.plain_test_password,
                password=new_password,
                password_confirm=new_password
            )
            res = self.client.post(url_for('user.change_password'), data=params)
            self.assert400(res)

            # Ensure password was changed
            self.assertTrue(self.cA.check_password(self.cA.plain_test_password))