/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HealthService {
    /**
     * Health check endpoint
     * @returns void
     * @throws ApiError
     */
    public static healthcheck(): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/healthz',
            errors: {
                504: `Database connection failed`,
            },
        });
    }
}
