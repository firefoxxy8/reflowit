'use strict';

/**
 * @ngdoc function
 * @name reflowitApp.controller:imagesCtrl
 * @description
 * # ReflowItCtrl
 * Controller of the reflowitApp
 */
angular.module('reflowitApp')

    .controller('ReflowItCtrl', function ($routeParams, $scope, ReflowIt) {

        $scope.reflowitObj = {
            status: 'idle',
            pdfUrl: null,
            refresh: false,
            response: null
        }

        $scope.doReflowIt = function() {
            console.log($scope.reflowitObj);
            $scope.reflowitObj.status = 'busy';
            $scope.reflowitObj.response = null
            ReflowIt.get($scope.reflowitObj.pdfUrl, $scope.reflowitObj.refresh).then(function (response) {
                $scope.reflowitObj.response = response;
                $scope.reflowitObj.status = 'idle';
                //console.log($scope.reflowit.response );
            });
        };

        if ($routeParams.url) {
            $scope.reflowitObj.pdfUrl = $routeParams.url;
            $scope.doReflowIt();
        }

    })

    .service("ReflowIt", function ($rootScope, $http, $q) {
        return {
            get: function (pdfUrl, refresh) {
                return helper(pdfUrl, refresh);
            }
        };
        function helper(pdfUrl, refresh, d) {
            var deferred = d || $q.defer();
            var url = $rootScope.apiEndpoint + '/?url=' + encodeURIComponent(pdfUrl);
            if (refresh) url += '&refresh=true';
            //console.log(url);
            $http.get(url).then(
                function (response) {
                    //console.log('status:',response.data.status);
                    if (response.data.status == 'ready') {
                        deferred.resolve(response.data);
                    } else {
                      setTimeout(function() {
                          return helper(pdfUrl, false, deferred);
                      }, 10000);
                    }
                },
                function (err) {
                    if (!d) {
                        return helper(pdfUrl, deferred);
                    } else {
                        deferred.reject(err);
                    }
                });
            return deferred.promise;
        }
    })

;
