/* Customers API Service */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { CustomerWithRepairCountResponse } from "../generated/data-contracts";

type CustomerResponse = CustomerWithRepairCountResponse;
export type { CustomerWithRepairCountResponse as CustomerResponse };

export interface CustomerCreate {
  vorname: string;
  nachname: string;
  telefon?: string | null;
  email?: string | null;
}

export class CustomersService {
  /**
   * List all customers
   */
  public static listCustomers(): CancelablePromise<{
    reply: string;
    data: CustomerResponse[];
    count: number;
  }> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/customers",
      errors: { 500: "Internal Server Error" },
    });
  }

  /**
   * Search customers by name, phone or email
   */
  public static searchCustomers(
    q: string,
  ): CancelablePromise<{ reply: string; data: CustomerResponse[] }> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/customers/search",
      query: { q },
      errors: { 500: "Internal Server Error" },
    });
  }

  /**
   * Create a new customer
   */
  public static createCustomer(
    body: CustomerCreate,
  ): CancelablePromise<{ reply: string; data: CustomerResponse }> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/customers",
      body,
      errors: { 400: "Bad Request", 500: "Internal Server Error" },
    });
  }

  /**
   * Get a single customer by ID
   */
  public static getCustomer(
    customerId: number,
  ): CancelablePromise<{ reply: string; data: CustomerResponse }> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/customers/{customer_id}",
      path: { customer_id: customerId },
      errors: { 404: "Not Found", 500: "Internal Server Error" },
    });
  }

  /**
   * Update a customer
   */
  public static updateCustomer(
    customerId: number,
    body: CustomerCreate,
  ): CancelablePromise<{ reply: string; data: CustomerResponse }> {
    return __request(OpenAPI, {
      method: "PUT",
      url: "/api/customers/{customer_id}",
      path: { customer_id: customerId },
      body,
      errors: {
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error",
      },
    });
  }

  /**
   * Delete a customer
   */
  public static deleteCustomer(
    customerId: number,
  ): CancelablePromise<{ reply: string; id: number }> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/customers/{customer_id}",
      path: { customer_id: customerId },
      errors: { 404: "Not Found", 500: "Internal Server Error" },
    });
  }
}
