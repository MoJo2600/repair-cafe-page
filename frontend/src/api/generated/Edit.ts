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

import { EditRepairParams, EditRepairWithTokenParams } from "./data-contracts";
import { HttpClient, RequestParams } from "./http-client";

export class Edit<
  SecurityDataType = unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @tags Web Pages
   * @name EditRepair
   * @summary Edit page for a repair record
   * @request GET:/edit/{id}
   */
  editRepair = ({ id }: EditRepairParams, params: RequestParams = {}) =>
    this.request<void, any>({
      path: `/edit/${id}`,
      method: "GET",
      ...params,
    });
  /**
   * No description
   *
   * @tags Web Pages
   * @name EditRepairWithToken
   * @summary Edit page for a repair record with token authentication
   * @request GET:/edit/{id}/{token}
   */
  editRepairWithToken = (
    { id, token }: EditRepairWithTokenParams,
    params: RequestParams = {},
  ) =>
    this.request<void, void>({
      path: `/edit/${id}/${token}`,
      method: "GET",
      ...params,
    });
}
