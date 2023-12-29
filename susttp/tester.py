from susttp.app import App

if __name__ == '__main__':
    # Test - kl
    app = App()
    test_routes = [
        '/upload',
        '/delete',
        '/<string:username>/<path:path>',
        '/<path>'
    ]
    queries = [
        '/upload?k1=v1#anchor',
        '/upload?',
        '/upload#anchorrr',
        '/upload?#anchorr',
        '/delete',
        '/upload?k1#anc',
        '/123',
        '/123/123',
        '/123/123/123',
        '/123/1233/',
    ]
    app.dynamic_route_items = [app.DynamicRouteItem(
        path=r, func=r
    ) for r in test_routes]
    print('BEGIN TEST')
    for q in queries:
        print('query ', q)
        request_param, path_param, func, anchor = app.route_handler(q)
        print('test end.')
        print('request_param=', request_param)
        print('path_param=', path_param)
        print('func=', func)
        print('anchor=', anchor)
