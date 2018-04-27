from flask import Blueprint, request, current_app, render_template

from sqlalchemy.exc import SQLAlchemyError

from POS.blueprints.base.app_view import AppView
from POS.models.base_model import AppDB
from POS.models.stock_management.supplier import Supplier


class SuppliersAPI(AppView):
    @staticmethod
    def get():
        try:
            suppliers = SuppliersAPI.get_all_suppliers()

            return render_template(
                template_name_or_list="suppliers.html",
                suppliers=suppliers
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return SuppliersAPI.error_in_processing_request()

    @staticmethod
    def put(supplier_id):
        if not supplier_id:
            return SuppliersAPI.send_response(
                msg="No supplier ID provided in the URL",
                status=400
            )

        # Capture request
        supplier_modification_request = request.get_json(silent=True)

        if not supplier_modification_request:
            return SuppliersAPI.error_in_request_response()

        # Validate the request
        if not SuppliersAPI.validate_supplier_modification_request(supplier_modification_request):
            return SuppliersAPI.validation_error_response()

        # Get info
        name = supplier_modification_request["name"].strip().lower()
        contact_person = supplier_modification_request["contact_person"].strip().lower()
        contact_number = supplier_modification_request["contact_number"]

        try:
            # Get the supplier
            supplier = AppDB.db_session.query(Supplier).filter(
                Supplier.id == supplier_id
            ).first()

            if not supplier:
                return SuppliersAPI.send_response(
                    msg="No supplier by that description",
                    status=404
                )

            supplier.name = name
            supplier.contact_person = contact_person
            supplier.contact_no = contact_number

            # Commit changes
            AppDB.db_session.commit()

            # Get update list of suppliers
            suppliers = SuppliersAPI.get_all_suppliers()

            return SuppliersAPI.send_response(
                msg=suppliers,
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return SuppliersAPI.error_in_processing_request()

    @staticmethod
    def delete(supplier_id):
        if not supplier_id:
            return SuppliersAPI.send_response(
                msg="No supplier ID provided in the URL",
                status=400
            )

        # Capture request
        supplier_deletion_request = request.get_json(silent=True)

        if not supplier_deletion_request:
            return SuppliersAPI.error_in_request_response()

        # Get the supplier
        supplier = AppDB.db_session.query(Supplier).get(supplier_id)

        try:
            # Check if supplier exists
            if not supplier:
                return SuppliersAPI.send_response(
                    msg="No supplier by that description",
                    status=404
                )

            # Remove supplier
            AppDB.db_session.delete(supplier)
            AppDB.db_session.commit()

            # Get the update list of suppliers
            suppliers = SuppliersAPI.get_all_suppliers()

            return SuppliersAPI.send_response(
                msg=suppliers,
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return SuppliersAPI.error_in_processing_request()

    @staticmethod
    def validate_supplier_modification_request(supplier_modification_request):
        if "name" in supplier_modification_request and \
                "contact_person" in supplier_modification_request and \
                "contact_number" in supplier_modification_request and \
                supplier_modification_request["name"] not in ("", None) and \
                supplier_modification_request["contact_person"] not in ("", None) and \
                supplier_modification_request["contact_number"] not in ("", None):
            return True
        return False

    @staticmethod
    def get_all_suppliers():
        suppliers = AppDB.db_session.query(Supplier).all()

        return [
            dict(
                id=supplier.id,
                name=supplier.name,
                contact_person=supplier.contact_person,
                contact_number=supplier.contact_no
            )for supplier in suppliers
        ]


class SupplierAPI(AppView):
    """
        API for the '/supplier' endpoint
    """
    @staticmethod
    def post():
        """
            Creates a new supplier
        :return:
        """
        # Capture request
        supplier_addition_request = request.get_json(silent=True)

        if not supplier_addition_request:
            return SupplierAPI.error_in_request_response()

        # Validate the request
        if not SupplierAPI.validate_supplier_addition_request(supplier_addition_request):
            return SupplierAPI.validation_error_response()

        # Get info
        name = supplier_addition_request["name"].strip().lower()
        contact_person = supplier_addition_request["contact_person"].strip().lower()
        contact_number = supplier_addition_request["contact_number"].strip().lower()

        try:
            # Model the supplier
            supplier = Supplier(
                name=name,
                contact_person=contact_person,
                contact_no=contact_number
            )

            # Add supplier
            AppDB.db_session.add(supplier)
            AppDB.db_session.commit()

            # Get update list of suppliers
            suppliers = SuppliersAPI.get_all_suppliers()

            return SupplierAPI.send_response(
                msg=dict(suppliers=suppliers),
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return SupplierAPI.error_in_processing_request()

    @staticmethod
    def validate_supplier_addition_request(supplier_addition_request):
        if "name" in supplier_addition_request and \
                "contact_person" in supplier_addition_request and \
                "contact_number" in supplier_addition_request and \
                supplier_addition_request["name"] not in ("", None) and \
                supplier_addition_request["contact_person"] not in ("", None) and \
                supplier_addition_request["contact_number"] not in ("", None):
            return True
        return False


# Supplier blueprint
supplier_view = SupplierAPI.as_view(name="supplier")
supplier_bp = Blueprint(
    name="supplier_bp",
    import_name=__name__,
    url_prefix="/supplier"
)
supplier_bp.add_url_rule(rule="", view_func=supplier_view, methods=["GET", "POST"])


# Suppliers blueprint
suppliers_view = SuppliersAPI.as_view(name="supplier")
suppliers_bp = Blueprint(
    name="suppliers_bp",
    import_name=__name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/suppliers"
)
suppliers_bp.add_url_rule(rule="", view_func=suppliers_view, methods=["GET"])
suppliers_bp.add_url_rule(rule="/<int:supplier_id>", view_func=suppliers_view, methods=["PUT", "DELETE"])
