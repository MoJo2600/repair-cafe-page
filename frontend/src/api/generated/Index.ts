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

import { HttpClient, RequestParams } from "./http-client";

export class Index<
  SecurityDataType = unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @tags Web Pages
   * @name IndexPage
   * @summary Root for Webpage. Renders index.html
   * @request GET:/index
   */
  indexPage = (params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/index`,
      method: "GET",
      ...params,
    });
}
