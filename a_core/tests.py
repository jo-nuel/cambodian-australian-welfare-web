from django.test import Client, TestCase, override_settings


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class SearchViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_page_loads_without_query(self):
        response = self.client.get('/search/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search CAWC NSW')

    def test_search_query_loads_without_error(self):
        response = self.client.get('/search/', {'q': 'Cambodian'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cambodian')

    def test_search_category_filter_loads_without_error(self):
        response = self.client.get('/search/', {'q': 'Cambodian', 'category': 'programs'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Category')
