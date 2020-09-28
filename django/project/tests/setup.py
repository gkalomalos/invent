from datetime import datetime
from random import randint

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from country.models import Country, Donor, CountryOffice
from user.models import Organisation, UserProfile
from user.tests import create_profile_for_user


class TestProjectData:
    def setUp(self):
        (self.project_data, self.org, self.country, self.country_office, self.d1, self.d2) = self.create_test_data(
            create_relations=True
        )

    def create_test_data(self, name: str = None, create_relations: bool = False, new_country_only: bool = False):
        if name is None:
            name = "Test Project1"

        if create_relations:
            org = Organisation.objects.create(name="org1")

            country = Country.objects.create(name="country1", code='CTR1',
                                             project_approval=True,
                                             region=Country.REGIONS[0][0],
                                             unicef_region=Country.UNICEF_REGIONS[0][0])

            country_office = CountryOffice.objects.create(
                name='Test Country Office',
                region=Country.UNICEF_REGIONS[0][0],
                country=country
            )

            d1 = Donor.objects.create(name="Donor1", code="donor1")
            d2 = Donor.objects.create(name="Donor2", code="donor2")
        else:
            if new_country_only:
                country_rand = randint(2, 9)
                country, _ = Country.objects.get_or_create(name=f'country{country_rand}', code=f'CTR{country_rand}',
                                                           project_approval=False,
                                                           region=Country.REGIONS[0][0],
                                                           unicef_region=Country.UNICEF_REGIONS[0][0])

                country_office = CountryOffice.objects.create(
                    name='Test Country Office',
                    region=Country.UNICEF_REGIONS[0][0],
                    country=country
                )
            else:
                country = self.country
                country_office = self.country_office
            org = self.org
            d1 = self.d1
            d2 = self.d2

        return {"project": {
            "date": datetime.utcnow(),
            "name": name,
            "organisation": org.id,
            "contact_name": "name1",
            "contact_email": "a@a.com",
            "implementation_overview": "overview",
            "overview": "new overview",
            "implementation_dates": "2016",
            "health_focus_areas": [1, 2],
            "geographic_scope": "somewhere",
            "country_office": country_office.id,
            "platforms": [1, 2],
            "donors": [d1.id, d2.id],
            "hsc_challenges": [1, 2],
            "start_date": str(datetime.today().date()),
            "end_date": str(datetime.today().date()),
            "field_office": 1,
            "goal_area": 1,
            "result_area": 1,
            "capability_levels": [],
            "capability_categories": [],
            "capability_subcategories": [],
            "dhis": [],
            "unicef_sector": [1, 2],
            "innovation_categories": [1, 2],
            "cpd": [1, 2],
            "regional_priorities": [1, 2],
            "hardware": [1, 2],
            "nontech": [1, 2],
            "functions": [1, 2],
            "phase": 1,
            "partners": [dict(partner_type=0, partner_name="test partner 1", partner_email="p1@partner.ppp",
                              partner_website="https://partner1.com"),
                         dict(partner_type=1, partner_name="test partner 2", partner_email="p2@partner.ppp",
                              partner_website="https://partner2.com")],
            "links": [dict(link_type=0, link_url="https://website.com"),
                      dict(link_type=1, link_url="https://sharepoint.directory")]
        }}, org, country, country_office, d1, d2

    def create_new_project(self, test_user_client=None):
        if test_user_client is None:
            test_user_client = self.test_user_client

        project_name = f"Test Project{randint(999, 999999)}"
        project_data, org, country, country_office, d1, d2 = self.create_test_data(name=project_name,
                                                                                   new_country_only=True)

        # Create project draft
        url = reverse("project-create", kwargs={"country_office_id": country_office.id})
        response = test_user_client.post(url, project_data, format="json")
        assert response.status_code == 201

        project_id = response.json().get("id")

        # Publish
        url = reverse("project-publish", kwargs={"project_id": project_id,
                                                 "country_office_id": country_office.id})
        response = test_user_client.put(url, project_data, format="json")
        assert response.status_code == 200

        return project_id, project_data, org, country, country_office, d1, d2


class MockRequest:
    user = None
    GET = {}
    COOKIES = {}


class SetupTests(TestProjectData, APITestCase):
    def setUp(self):
        super().setUp()
        # Create a test user with profile.
        user_email = "test_user@unicef.org"

        url = reverse("rest_register")
        data = {
            "email": user_email,
            "password1": "123456hetNYOLC",
            "password2": "123456hetNYOLC"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201, response.json())

        create_profile_for_user(response)

        # Log in the user.
        url = reverse("api_token_auth")
        data = {
            "username": user_email,
            "password": "123456hetNYOLC"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.json())
        self.test_user_key = response.json().get("token")
        self.test_user_client = APIClient(HTTP_AUTHORIZATION="Token {}".format(self.test_user_key), format="json")
        self.user_profile_id = response.json().get('user_profile_id')

        # Update profile.
        self.country_id = self.country.id
        self.country.name_en = 'Hungary'
        self.country.name_fr = 'Hongrie'
        self.country.save()

        url = reverse("userprofile-detail", kwargs={"pk": self.user_profile_id})
        data = {
            "name": "Test Name",
            "organisation": self.org.id,
            "country": self.country_id}
        response = self.test_user_client.put(url, data)
        self.assertEqual(response.status_code, 200, response.json())
        self.user_profile_id = response.json().get('id')

        self.userprofile = UserProfile.objects.get(id=self.user_profile_id)
        self.country.users.add(self.userprofile)

        # Create project draft
        url = reverse("project-create", kwargs={"country_office_id": self.country_office.id})
        response = self.test_user_client.post(url, self.project_data, format="json")
        self.assertEqual(response.status_code, 201, response.json())

        self.project_id = response.json().get("id")

        # Publish
        url = reverse("project-publish", kwargs={"project_id": self.project_id,
                                                 "country_office_id": self.country_office.id})
        response = self.test_user_client.put(url, self.project_data, format="json")
        self.assertEqual(response.status_code, 200, response.json())

    def check_project_search_init_state(self, project):
        obj = project.search
        self.assertEqual(obj.project_id, project.id)

        for field in obj._meta.fields:
            if field.name not in ('created', 'modified', 'project'):
                self.assertEqual(getattr(obj, field.name), field.get_default())
