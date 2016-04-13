'use strict';

/**
 * @ngdoc overview
 * @name reflowitApp
 * @description
 * # reflowitApp
 *
 * Main module of the application.
 */
angular
    .module('reflowitApp', [
        'ngAnimate',
        'ngCookies',
        'ngResource',
        'ngRoute',
        'ngSanitize',
        'ngTouch',
        'base64',
        'ui.bootstrap',
        'ngPrettyJson'
    ])

    .run(function ($rootScope) {

        $rootScope.apiEndpoint = 'https://kvc2558vpl.execute-api.us-east-1.amazonaws.com/prod/reflowit-lambda-api';

    })

  .config(function ($routeProvider, $locationProvider) {

        $routeProvider
            .when('/about', {
                templateUrl: 'views/about.html',
                controller: 'AboutCtrl',
                controllerAs: 'about'
            })
            .when('/', {
                templateUrl: 'views/reflowit/index.html',
                controller: 'ReflowItCtrl',
                controllerAs: 'reflowit'
            })

            .otherwise({
                redirectTo: '/'
            })
            //$locationProvider.html5Mode(true);
    })

    .directive('navMenu', function ($location) {
        return function (scope, element, attrs) {
            var links = element.find('a'),
                currentLink,
                urlMap = {},
                activeClass = attrs.navMenu || 'active';

            for (var i = links.length - 1; i >= 0; i--) {
                var link = angular.element(links[i]);
                var url = link.attr('href');
                if (url.substring(0, 1) === '#') {
                    urlMap[url.substring(1)] = link;
                } else {
                    urlMap[url] = link;
                }
            }

            scope.$on('$routeChangeStart', function () {
                var path = urlMap[$location.path()];
                links.parent('li').removeClass(activeClass);
                if (path) {
                    path.parent('li').addClass(activeClass);
                }
            });
        };
    })

;
