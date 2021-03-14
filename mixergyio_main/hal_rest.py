import json
import requests


TIMEOUT=60



class Resource:
    def __init__(self, obj):
        if isinstance(obj, Resource):
            self.__obj = obj.__obj  #get_obj()
        else:
            self.__obj = obj


    def __getitem__(self, val):
        return self.__obj.__getitem__(val)


    def __repr__(self):
        return str(self.__obj)


    def get_obj(self):
        return self.__obj


    def get_link(self, link):
        return self.__obj['_links'][link]['href']


    def get_links(self):
        return self.__obj['_links']


    def get_list(self, list):
        try:
            return self.__obj['_embedded'][list]
        except KeyError:
            pass

    def get_lists(self):
        try:
            return self.__obj['_embedded']
        except KeyError:
            pass



class HAL_REST:
    def __init__(self, host, verify=None):
        self.__url_root = 'https://{}'.format(host)
        self.__session = requests.Session()
        if verify is not None:
            self.__session.verify = verify


    def __enter__(self):
        return self


    def __exit__(self, *exc_info):
        self.close()



    def close(self):
        self.__session.close()


    def get_url_root(self):
        return self.__url_root


    def _set_header(self, header, value):
        self.__session.headers.update({header: value})


    def delete(self, url, **kwargs):
        kwargs.setdefault('timeout', TIMEOUT)
        r = self.__session.delete(url, **kwargs)
        r.raise_for_status()
        return r


    def get(self, url, **kwargs):
#        print('URL:', url)
        kwargs.setdefault('timeout', TIMEOUT)
        r = self.__session.get(url, **kwargs)
        r.raise_for_status()
        return r


    def post(self, url, **kwargs):
        kwargs.setdefault('timeout', TIMEOUT)
        r = self.__session.post(url, **kwargs)
        r.raise_for_status()
        return r


    def put(self, url, **kwargs):
        kwargs.setdefault('timeout', TIMEOUT)
        r = self.__session.put(url, **kwargs)
        r.raise_for_status()
        return r



    def get_hal_root(self):
        return Resource(self.get('{}/api/v2'.format(self.__url_root)).json())


    def get_hal_resource(self, *href, **kwargs):
        return Resource(self.get_hal_json(*href, **kwargs))


    def get_hal_json(self, *href, **kwargs):
        return self.get_hal(*href, **kwargs).json()


    def get_hal(self, *href, **kwargs):
        url = self.__get_hal_url(*href, **kwargs)
        return self.get(url, **kwargs)


    def delete_hal(self, *href, **kwargs):
        url = self.__get_hal_url(*href, **kwargs)
        return self.delete(url, **kwargs)


    def post_hal(self, *href, **kwargs):
        url = self.__get_hal_url(*href, **kwargs)
        return self.post(url, **kwargs)


    def put_hal(self, *href, **kwargs):
        url = self.__get_hal_url(*href, **kwargs)
        return self.put(url, **kwargs)


#     def get_embedded_list(self, hal, *href, **kwargs):
#         list_name = href[-1]
#         href = href[:-1]
# 
#         resource = self.get_hal_json(root, *href, **kwargs)
# 
#         if '_embedded' in resource:
#             list = resource['_embedded'][list_name]
#         else:
#             list = []
# 
#         return list


    def __get_hal_url(self, *href, **kwargs):
        if len(href) == 0:
            raise RuntimeError('No resource supplied')

        if isinstance(href[0], Resource):
            hal = href[0]
            href = href[1:]
            if len(href) == 0:
                href = ('self', )
        else:
            hal = self.get_hal_root()

        while len(href) > 1:
            h = href[0]
            href = href[1:]
            hal = Resource(self.get(hal.get_link(h), **kwargs).json())

        return hal.get_link(href[0])
