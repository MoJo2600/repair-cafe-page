/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class WebPagesService {
    /**
     * Edit page for a repair record
     * @param id
     * @returns any Edit page
     * @throws ApiError
     */
    public static editRepair(
        id: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/edit/{id}',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Edit page for a repair record with token authentication
     * @param id
     * @param token
     * @returns any Edit page
     * @throws ApiError
     */
    public static editRepairWithToken(
        id: number,
        token: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/edit/{id}/{token}',
            path: {
                'id': id,
                'token': token,
            },
            errors: {
                403: `Invalid token`,
            },
        });
    }
    /**
     * Root for Webpage. Renders index.html
     * @returns any Main page
     * @throws ApiError
     */
    public static indexPage(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/index',
        });
    }
    /**
     * Display all repairs in a table format
     * @returns any HTML page displaying all repairs in a table
     * @throws ApiError
     */
    public static listRepairs(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/list',
            errors: {
                500: `Internal Server Error - database query failed`,
            },
        });
    }
    /**
     * Get statistics data for charts
     * @param type
     * @returns any Statistics data
     * @throws ApiError
     */
    public static getStatData(
        type: 'repairs' | 'devices' | 'time',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/stat-data/{type}',
            path: {
                'type': type,
            },
        });
    }
    /**
     * Serve the Vue.js application
     * @returns any Vue.js application
     * @throws ApiError
     */
    public static vueApp(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/vue',
        });
    }
}
