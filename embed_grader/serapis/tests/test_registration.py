from django.test import TestCase, Client
from django.contrib.auth.models import User
from serapis.models import UserProfile
from django.db.utils import IntegrityError

class RegistrationTestCase(TestCase):
	def setUp(self):
		self.client = Client()

	def test_user_should_be_able_to_register(self):
		# The client posts the form
		response = self.client.post('/registration/', {
			'first_name': 'Xi',
			'last_name': 'Han',
			'username': 'xihan94',
			'email': 'xihan94@ucla.edu',
			'uid': '504136747',
			'password1': 'acmilan22',
			'password2': 'acmilan22',
			})

		self.assertEquals(response.status_code, 200)

		## TODO: test for activation and what's following
		
