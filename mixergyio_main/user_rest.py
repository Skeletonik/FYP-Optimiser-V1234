import json
import requests



from hal_rest import Resource, HAL_REST


class ListPortfolio(Resource):
    def __init__(self, obj):
        super().__init__(obj)


class Portfolio(ListPortfolio):
    def __init__(self, obj):
        super().__init__(obj)


class Setting(Resource):
    def __init__(self, obj):
        super().__init__(obj)


class ListTank(Resource):
    def __init__(self, obj):
        super().__init__(obj)


class Tank(ListTank):
    def __init__(self, obj):
        super().__init__(obj)


class ListUser(Resource):
    def __init__(self, obj):
        super().__init__(obj)


class User(ListUser):
    def __init__(self, obj):
        super().__init__(obj)



class UserREST(HAL_REST):
    """Helper class for accessing Mixergy REST API
    """

    def __init__(self, host='www.mixergy.io', username="damon@owensquare.coop", password="SyM818^M5h", verify=None, logout_on_exit=True):
        """Create dict, log in if credentials are supplied

        Parameters
        ----------
        host : string
            Machine hosting REST API
        username : string
            Username (email address)
        password : string
            User's password
        logout_on_exit : boolean
            When used as a context manager, indicates whether this dict should log out on exit
        """
        super().__init__(host, verify=verify)

        self.__logout_on_exit = False

        if username is not None:
            self.login(username, password, logout_on_exit=logout_on_exit)


    def __exit__(self, *exc_info):
        if self.__logout_on_exit:
            self.logout()
        super().__exit__(*exc_info)



    def get_token(self):
        """Get the current authentication token

        Returns
        -------
        string
            The current authentication token. These are created by a login request

        """
        return self.__token



    def set_token(self, token):
        """Set the current authentication token

        Parameters
        ----------
        token : string
            Set the current login token. Usually obtained by a login request performed by a previous instance of this class. 
        """
        self.__token = token
        self._set_header('Authorization', 'Bearer ' + token)



    def logout(self):
        self.delete_hal('account', 'login')
        self.__logout_on_exit = False


    def logout_on_exit(self, logout_on_exit):
        self.__logout_on_exit = logout_on_exit



    def login(self, username, password, logout_on_exit=True):
        r = self.post_hal('account', 'login', json={'username': username,'password': password})

        self.__logout_on_exit = logout_on_exit
    
        token = r.json()['token']

        self.set_token(token)

        if token is None:
            raise RuntimeError('Login token not available')

        return r



    def get_tanks(self):
        """Get the tanks visible to the user

        Return
        ------
        dictionary
            Get the user's tanks as a dictionary. The key is the tank serial number, the value is the Tank dict.
        """
        tanks = self.get_hal_resource('tanks').get_list('tankList')

        if tanks is not None:
            return { tank['serialNumber']: ListTank(tank) for tank in tanks }


    def get_tank(self, tank):
        """Get the tanks visible to the user

        Parameters
        ----------
        tank : string|Tank
            If this is a Tank dict fetch the HAL resource for the tank. If this is a string, fetch all tanks and extract the Tank dict before fetching the HAL resource  .


        Return
        ----------
        Tank
            Get the user's tanks as a dictionary. The key is the tank serial number. 
        """
        if not isinstance(tank, ListTank):
            tanks = self.get_tanks()
            tank = tanks[tank]

        return Tank(self.get_hal_json(tank))


    def get_tank_settings(self, tank):
        """Get the tank's settings

        Parameters
        ----------
        tank : Tank
            The tank for which to fetch the settings.


        Return
        ----------
        dict
            Get the tank's as a Python dict. 
        """
        self.__check_tank(tank)

        return self.get_hal_json(tank, 'settings')


    def put_tank_settings(self, tank, settings):
        """Pet the tank's settings

        Parameters
        ----------
        tank : Tank
            The tank for which to set the settings.
        settings : dictionary
            Tank settings as a dictionary


        Return
        ----------
        dict
            The response to the request 
        """
        self.__check_tank(tank)

        return self.put_hal(tank, 'settings', json=settings)


    def get_tank_measurements(self, tank, start=None, end=None):
        """Get the tank's measurement

        Parameters
        ----------
        tank : Tank
            The tank for which to fetch the measurements.
        start : int
            The fetch start time in milliseconds

        Return
        ----------
        dict
            Measurement data
        """
        self.__check_tank(tank)

        params = { 'size': 2000 }

        if start is not None and end is not None:
            params['range'] = '{}:{}'.format(start, end)

        return self.get_hal_json(tank, 'measurements', params=params)


    def get_tank_earliest_measurement(self, tank):
        """Get the tank's earliest measurement

        Parameters
        ----------
        tank : Tank
            The tank for which to fetch the settings.
        start : int
            The fetch start time in milliseconds

        Return
        ----------
        dict
            Measurement data
        """
        self.__check_tank(tank)
        return self.get_hal_json(tank, 'earliest_measurement')


    def get_tank_latest_measurement(self, tank):
        """Get the tank's settings

        Parameters
        ----------
        tank : Tank
            The tank for which to fetch the settings.


        Return
        ----------
        dict
            Get the tank's as a Python dict. 
        """
        self.__check_tank(tank)

        return self.get_hal_json(tank, 'latest_measurement')


    def get_tank_schedule(self, tank):
        """Get the tank's settings

        Parameters
        ----------
        tank : Tank
            The tank for which to fetch the settings.


        Return
        ----------
        dict
            Get the tank's as a Python dict. 
        """
        self.__check_tank(tank)
        return self.get_hal_json(tank, 'schedule')

 
    def put_tank_schedule(self, tank, schedule):
        self.__check_tank(tank)
        return self.put_hal(tank, 'schedule', json=schedule)

 
    def get_tank_auto_schedule(self, tank):
        self.__check_tank(tank)
        return self.get_hal_json(tank, 'autoschedule')
 
 
    def put_tank_auto_schedule(self, tank, schedule):
        self.__check_tank(tank)
        return self.put_hal(tank, 'autoschedule', json=schedule)


    def get_tank_tariff(self, tank):
        self.__check_tank(tank)
        return self.get_hal_json(tank, 'tariff')
 

    def put_tank_tariff(self, tank, tariff):
        self.__check_tank(tank)
        return self.put_hal(tank, 'tariff', json=tariff)

 
    def put_tank_control(self, tank, control):
        """Get the tank's settings

        Parameters
        ----------
        tank : Tank
            The tank for which to fetch the settings.


        Return
        ----------
        dict
            Get the tank's as a Python dict. 
        """
        self.__check_tank(tank)
        return self.put_hal(tank, 'control', json=control)


    def get_tank_commission_record(self, tank):
        self.__check_tank(tank)

        return self.get_hal_json(tank, 'commission')


    def create_tank_commission_record(self, tank):
        self.__check_tank(tank)

        return Resource(self.post_hal(tank, 'commission').json())



    def get_portfolios(self):
        portfolios = self.get_hal_resource('portfolios').get_list('portfolioList')

        return { portfolio['portfolioName']: ListPortfolio(portfolio) for portfolio in portfolios }



    def get_portfolio(self, portfolio):
        if not isinstance(portfolio, ListPortfolio):
            portfolios = self.get_portfolios()
            portfolio = portfolios[portfolio]

        return Portfolio(self.get_hal_resource(portfolio))



    def get_portfolio_tanks(self, portfolio):
        self.__check_portfolio(portfolio)

        tanks = self.get_hal_resource(portfolio, 'tanks').get_list('tankList')

        if tanks is not None:
            return { tank['id']: Tank(tank) for tank in tanks }



    def create_portfolio(self, name, description, identifier):
        payload = {'portfolioName': name, 'portfolioDescription': description, 'portfolioId': identifier}
        return self.post_hal('portfolios', json=payload)



    def delete_portfolio(self, name):
        portfolios = self.get_portfolios()
        payload = {'name': name}
        return self.delete_hal_target(portfolios[name])



    def portfolio_add_user(self, portfolio, username, role):
        self.__check_portfolio(portfolio)
        payload = {'username':username, 'role': role}
        return self.post_hal(portfolio, 'users', json=payload)



    def portfolio_add_tank(self, portfolio, tankId):
        self.__check_portfolio(portfolio)
        payload = {'tankIdentifier':tankId}
        return self.post_hal(portfolio, 'tanks', json=payload)



    def get_system_settings(self):
        settings = self.get_hal_resource('system', 'settings').get_list('settingList')

        return { setting['name']: Setting(setting) for setting in settings }


    def get_system_setting(self, setting):
        self.__check_setting(setting)
        return self.get_hal_json(setting)



    def put_system_setting(self, setting, json=None, data=None):
        self.__check_setting(setting)
        return self.put_hal(setting, json=json, data=data)


    def get_users_me(self):
        return User(self.get_hal_resource('users', 'me'))


    def get_anomalies(self, start=None, end=None):
        params = None

        if start is not None and end is not None:
            params = { 'params': '{}:{}'.format(start, end) }

        return self.get_hal_resource('data', 'anomalies', params=params)


    def get_summaries(self):
        ps = self.get_hal_resource('data', 'summaries').get_list('portfolioList')

        return { p['portfolioName']: Resource(p) for p in ps}


    def get_summary(self, summary):
        return self.get_hal_resource(summary)


    def get_summary_measurements(self, portfolio, start=None, end=None):
        params = { 'size': 2000 }

        if start is not None and end is not None:
            params['range'] = '{}:{}'.format(start, end)

        return self.get_hal_json(portfolio, 'measurements', params=params)



    def associate_tank(self, user, id, asc=None):
        self.__check_user(user)
        settings = {'tankIdentifier': id}
        if asc is not None:
            settings['automatic_schedule_control'] = asc
        return  self.post_hal(user, 'tanks', json=settings)


    def create_user(self, account_data):
        return self.post_hal('account', json=account_data)


    def post_validate(self, payload):
        return self.post_hal('account', 'validation', json=payload)


    def put_validate(self, payload):
        return self.put_hal('account', 'validation', json=payload)


    def post_firmware(self, data):
        r = self.post_hal('firmware', files=data)
        r.raise_for_status()
        return r


    def put_set_firmware_version(self, version, ids):
        payload = {'firmwareVersion': version, 'tankIds' : ids}
        return self.put_hal('tanks', 'firmware', json=payload)


    def put_change_password(self, user, password, new_password):
        self.__check_user(user)
        payload = {'oldPassword': password, 'newPassword': new_password}
        return self.put_hal(user, 'password', json=payload)


    def post_password_reset(self, username):
        payload = {'username': username}
        return self.post_hal('account', 'passwordreset', json=payload)

    
    def put_password_reset(self, code, password):
        payload = { 'code' : code, 'newPassword': password }
        return self.put_hal('account', 'passwordreset', json=payload)


    def get_users(self):
        users = self.get_hal_resource('users').get_list('userList')

        return { user['username']: ListUser(user) for user in users }


    def get_user(self, user):
        if not isinstance(user, ListUser):
            users = self.get_users()
            user = users[user]

        return User(self.get_hal_json(user))


    def get_user_tanks(self, user):
        self.__check_user(user)

        tanks = self.get_hal_resource(user, 'tanks').get_list('tankList')

        if tanks is not None:
            return { tank['serialNumber']: ListTank(tank) for tank in tanks }


    @classmethod
    def __check_portfolio(cls, portfolio):
        if not isinstance(portfolio, Portfolio):
            raise RuntimeError('portfolio ({}) is not a Portfolio'.format(portfolio))


    @classmethod
    def __check_setting(cls, setting):
        if not isinstance(setting, Setting):
            raise RuntimeError('setting ({}) is not a Setting'.format(setting))


    @classmethod
    def __check_tank(cls, tank):
        if not isinstance(tank, Tank):
            raise RuntimeError('tank ({}) is not a Tank'.format(tank))


    @classmethod
    def __check_user(cls, user):
        if not isinstance(user, User):
            raise RuntimeError('user ({}) is not a User'.format(user))
