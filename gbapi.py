import copy
import defusedxml
import json
import requests
import time


HOST = "https://www.giantbomb.com/"

ENDPOINTS = {
    "CATEGORIES" : "api/video_categories/",
    "VIDEOS" : "api/videos/",
}

DEFAULT_DELAY_BETWEEN_CALLS = .5

DEFAULT_USER_AGENT = 'gbapi'

class APIException(Exception):
    pass

class APIItem:
    def __init__(self, data, format):
        self._format = format
        self._raw = data
        if format == 'json':
            self._data = json.loads(data)
        elif format == 'xml':
            self._data = defusedxml.fromstring(data)
        else:
            raise NotImplementedError()

    def data(self):
        return copy.deepcopy(self._data)

    def format(self):
        return self._format

    def raw(self):
        return self._raw

class VideoCategory(APIItem):
    def __init__(self, data, format):
        raise NotImplementedError()

class PaginatedResource:
    def __init__(self, api_key, resource_class, user_agent = DEFAULT_USER_AGENT, format = 'json', \
        delay_between_calls = DEFAULT_DELAY_BETWEEN_CALLS, host = HOST, endpoint ="", \
        additional_headers = {}, additional_params = {}, use_cache = True):

        self._api_key = api_key
        self._delay_between_calls = delay_between_calls
        self._endpoint = endpoint
        self._format = format
        self._host = host
        self._next_item = 0
        self._resource_class = resource_class
        self._use_cache = use_cache

        self._params = additional_params.copy()
        self._params['api_key'] = self._api_key
        self._params['format'] = self._format

        self._headers = additional_headers.copy()
        self._headers['User-Agent'] = user_agent

        self.flush_cache()
        self._time_of_last_call = time.time()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            item = self.item(self._next_item)
            self._next_item += 1
            return item
        except IndexError as index_error:
            raise StopIteration()

    def _extract_data_from_page(self, page):
        data = {'resources' : [], 'number_of_items' : None, 'items_per_page' : None}

        if self._format == "json":
            json_data = json.loads(page)
            if json_data['error'] != 'OK':
                raise APIException()
            data['number_of_items'] = json_data['number_of_total_results']
            data['items_per_page'] = json_data['limit']
            for result in json_data['results']:
                data['resources'].append(json.dumps(result))
        elif self._format == "xml":
            xml_data = defusedxml.fromstring(page)
            if xml_data.find('error').text.strip() != 'OK':
                raise APIException()
            data['number_of_items'] = int(xml_data.find('number_of_total_results').text)
            data['items_per_page'] = int(xml_data.find('limit').text)
            for result in xml_data.find('results'):
                data['resources'].append(ElementTree.tostring(result))
            else:
                raise NotImplementedError()

        return data

    def _get_page(self, index, total_number_of_items = None, number_of_items_per_page = None):
        if self._use_cache:
            if index in self._page_cache:
                return self._page_cache[index]

        if index == 0:
            self._params['offset'] = 0
        else:
            if total_number_of_items is None or number_of_items_per_page is None:
                raise Exception()
            offset = index * number_of_items_per_page
            if offset >= total_number_of_items:
                raise IndexError()
            self._params['offset'] = offset
        time_since_last_call = time.time() - self._time_of_last_call
        if time_since_last_call < self._delay_between_calls:
            time.sleep(self._delay_between_calls - time_since_last_call)

            try:
                response = requests.get(self._host +  self._endpoint, params = self._params, \
                            headers = self._headers)
                response.raise_for_status()
                self._time_of_last_call = time.time()
            except:
                raise APIException()

        self._time_of_last_call = time.time()
        self._page_cache[index] = response.text

        return self._page_cache[index]

    def _get_resource(self, index):
        page_zero = None
        page_zero_data = None

        if self._total_number_of_items is None or self._number_of_items_per_page is None or \
        not self._use_cache:
            page_zero = self._get_page(0)
            page_zero_data = self._extract_data_from_page(page_zero)
            number_of_items = page_zero_data['number_of_items']
            items_per_page = page_zero_data['items_per_page']
            self._total_number_of_items = number_of_items
            self._number_of_items_per_page = items_per_page
        else:
            if index in self._resource_cache:
                return self._resource_cache[index]

        page_index, item_index_in_page = divmod(index, self._number_of_items_per_page)
        page = self._get_page(  page_index, \
        total_number_of_items = self._total_number_of_items, \
        number_of_items_per_page = self._number_of_items_per_page)

        page_data = self._extract_data_from_page(page)
        first_index_on_page = page_index * self._number_of_items_per_page
        for resource_index, resource in enumerate(page_data['resources']):
            self._resource_cache[first_index_on_page + resource_index] = resource

        return page_data['resources'][item_index_in_page]

    def item(self, index):
        return self._resource_class(self._get_resource(index), format = self._format)

    def raw_page(self, index):
        if self._total_number_of_items is None or self._number_of_items_per_page is None or \
        not self._use_cache:
            page_zero = self._get_page(0)
            page_zero_data = self._extract_data_from_page(page_zero)
            number_of_items = page_zero_data['number_of_items']
            items_per_page = page_zero_data['items_per_page']
            self._total_number_of_items = number_of_items
            self._number_of_items_per_page = items_per_page
            if index == 0:
                return page_zero

        return self._get_page(  index, total_number_of_items = self._total_number_of_items, \
                                number_of_items_per_page = self._number_of_items_per_page)

    def reset_iteration(self):
        self._next_item = 0

    def flush_cache(self):
        self._page_cache = {}
        self._resource_cache = {}
        self._total_number_of_items = None
        self._number_of_items_per_page = None
