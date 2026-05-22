"""
Customers API endpoints.
"""

import json

from flask import Blueprint, Response, current_app, request
from sqlalchemy import func, or_

from app.extensions import db
from app.models import Customer, Repair
from app.schemas import (
    CustomerCreate,
    CustomerResponse,
    CustomerWithRepairCountResponse,
)
from app.validation import validate_request

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers", methods=["GET"])
def api_list_customers():
    """List all customers with their repair count.
    ---
    operationId: listCustomers
    tags:
      - Customers
    responses:
      200:
        description: List of customers with repair counts
        schema:
          type: object
          properties:
            reply:
              type: string
            data:
              type: array
              items:
                $ref: '#/components/schemas/CustomerWithRepairCountResponse'
            count:
              type: integer
      500:
        description: Internal Server Error
    """
    try:
        rows = (
            db.session.query(Customer, func.count(Repair.id).label("repair_count"))
            .outerjoin(Repair, Repair.customer_id == Customer.id)
            .group_by(Customer.id)
            .order_by(Customer.nachname, Customer.vorname)
            .all()
        )
        data = []
        for customer, repair_count in rows:
            d = CustomerWithRepairCountResponse(
                **CustomerResponse.model_validate(customer).model_dump(),
                repair_count=repair_count,
            ).model_dump(mode="json")
            data.append(d)
        return Response(
            json.dumps({"reply": "done", "data": data, "count": len(data)}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error listing customers: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@customers_bp.route("/customers/search", methods=["GET"])
def api_search_customers():
    """Search customers by name, phone or email."""
    q = request.args.get("q", "").strip()
    if not q:
        return Response(
            json.dumps({"reply": "done", "data": []}),
            status=200,
            mimetype="application/json",
        )

    try:
        like = f"%{q}%"
        customers = (
            Customer.query.filter(
                or_(
                    Customer.vorname.ilike(like),
                    Customer.nachname.ilike(like),
                    db.func.concat(Customer.vorname, " ", Customer.nachname).ilike(
                        like
                    ),
                    Customer.telefon.ilike(like),
                    Customer.email.ilike(like),
                )
            )
            .order_by(Customer.nachname, Customer.vorname)
            .limit(20)
            .all()
        )

        data = [
            CustomerResponse.model_validate(c).model_dump(mode="json")
            for c in customers
        ]
        return Response(
            json.dumps({"reply": "done", "data": data}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error searching customers: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@customers_bp.route("/customers", methods=["POST"])
@validate_request(CustomerCreate)
def api_create_customer(validated_data: CustomerCreate):
    """Create a new customer."""
    try:
        customer = Customer(
            vorname=validated_data.vorname,
            nachname=validated_data.nachname,
            telefon=validated_data.telefon,
            email=str(validated_data.email) if validated_data.email else None,
        )
        db.session.add(customer)
        db.session.commit()
        data = CustomerResponse.model_validate(customer).model_dump(mode="json")
        return Response(
            json.dumps({"reply": "done", "data": data}),
            status=201,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating customer: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@customers_bp.route("/customers/<int:customer_id>", methods=["GET"])
def api_get_customer(customer_id: int):
    """Get a single customer by ID."""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = CustomerResponse.model_validate(customer).model_dump(mode="json")
        return Response(
            json.dumps({"reply": "done", "data": data}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error getting customer {customer_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@customers_bp.route("/customers/<int:customer_id>", methods=["PUT"])
@validate_request(CustomerCreate)
def api_update_customer(validated_data: CustomerCreate, customer_id: int):
    """Update a customer."""
    try:
        customer = Customer.query.get_or_404(customer_id)
        customer.vorname = validated_data.vorname
        customer.nachname = validated_data.nachname
        customer.telefon = validated_data.telefon
        customer.email = str(validated_data.email) if validated_data.email else None
        db.session.commit()
        data = CustomerResponse.model_validate(customer).model_dump(mode="json")
        return Response(
            json.dumps({"reply": "done", "data": data}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating customer {customer_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@customers_bp.route("/customers/<int:customer_id>", methods=["DELETE"])
def api_delete_customer(customer_id: int):
    """Delete a customer (sets customer_id to NULL on linked repairs)."""
    try:
        customer = Customer.query.get_or_404(customer_id)
        # Detach repairs rather than cascading delete
        Repair.query.filter_by(customer_id=customer_id).update({"customer_id": None})
        db.session.delete(customer)
        db.session.commit()
        return Response(
            json.dumps({"reply": "done", "id": customer_id}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting customer {customer_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )
