/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

import { GetStatDataParams } from "./data-contracts";
import { HttpClient, RequestParams } from "./http-client";

export class StatData<
  SecurityDataType = unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @tags Web Pages
   * @name GetStatData
   * @summary Get statistics data for charts
   * @request GET:/stat-data/{type}
   */
  getStatData = ({ type }: GetStatDataParams, params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/stat-data/${type}`,
      method: "GET",
      ...params,
    });
}
