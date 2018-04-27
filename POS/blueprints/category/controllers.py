from flask import Blueprint, request, session, current_app
from flask_login import login_required

from sqlalchemy.exc import SQLAlchemyError

from typing import List

from POS.blueprints.base.app_view import AppView

from POS.models.base_model import AppDB
from POS.models.stock_management.category import Category
from POS.models.user_management.business import Business

from POS.utils import is_admin


class CategoryAPI(AppView):
    @staticmethod
    @login_required
    def get():
        try:
            # Get full lists of categories
            categories = CategoryAPI.get_all_categories()

            return CategoryAPI.send_response(
                msg=dict(categories=categories),
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return CategoryAPI.error_in_processing_request()

    @staticmethod
    @login_required
    @is_admin
    def post():
        new_categories_request = request.get_json(silent=True)

        if not new_categories_request:
            return CategoryAPI.error_in_request_response()

        # Ensure request has all fiends filled
        if not CategoryAPI.validate_new_categories_request(new_categories_request):
            return CategoryAPI.validation_error_response()

        # Fetch the info
        name = new_categories_request["name"].strip().lower()
        description = new_categories_request["description"].strip().lower()

        try:
            # Create category instance
            category = Category(name, description)

            # Associate the category with the business
            business = AppDB.db_session.query(Business).get(session["business_id"])
            category.business = business

            # Add and commit instance
            AppDB.db_session.add(category)
            AppDB.db_session.commit()

            # Get full lists of categories
            categories = CategoryAPI.get_all_categories()

            return CategoryAPI.send_response(
                msg=dict(categories=categories),
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return CategoryAPI.error_in_processing_request()

    @staticmethod
    @login_required
    @is_admin
    def put():
        new_categories_request = request.get_json(silent=True)

        if not new_categories_request:
            return CategoryAPI.send_response(
                msg="Problem with request type or structure",
                status=400
            )

        # Ensure request has all fields filled
        if not CategoryAPI.validate_edit_category_request(new_categories_request):
            return CategoryAPI.send_response(
                msg="Missing fields or values",
                status=400
            )

        # Fetch the info
        category_id = new_categories_request["id"].strip().lower()
        name = new_categories_request["name"].strip().lower()
        description = new_categories_request["description"].strip().lower()

        try:
            # Get category
            category = CategoryAPI.get_category_within_business(category_id)

            if not category:
                return CategoryAPI.send_response(
                    msg="No category by that description",
                    status=404
                )

            # Edit the fields
            category.name = name
            category.description = description

            # Commit changes
            AppDB.db_session.commit()

            # Get updated list of categories
            categories = CategoryAPI.get_all_categories()

            return CategoryAPI.send_response(
                msg=dict(categories=categories),
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return CategoryAPI.error_in_processing_request()

    @staticmethod
    @login_required
    @is_admin
    def delete():
        new_categories_request = request.get_json(silent=True)

        if not new_categories_request:
            return CategoryAPI.send_response(
                msg="Problem with request type or structure",
                status=400
            )

        # Ensure request has all fields filled
        if not CategoryAPI.validate_delete_category_request(new_categories_request):
            return CategoryAPI.send_response(
                msg="Missing fields or values",
                status=400
            )

        # Get info
        category_id = new_categories_request["id"]

        try:
            # Get the category to delete
            category = CategoryAPI.get_category_within_business(category_id)

            if not category:
                return CategoryAPI.send_response(
                    msg="No category by that description",
                    status=404
                )

            # Delete the category
            AppDB.db_session.delete(category)
            AppDB.db_session.commit()

            # Get updated list of categories
            categories = CategoryAPI.get_all_categories()

            return CategoryAPI.send_response(
                msg=dict(categories=categories),
                status=200
            )
        except SQLAlchemyError as e:
            AppDB.db_session.rollback()
            current_app.logger.error(e)
            current_app.sentry.captureException()
            return CategoryAPI.error_in_processing_request()

    @staticmethod
    def validate_delete_category_request(new_categories_request: request) -> bool:
        if "id" in new_categories_request and \
                new_categories_request["id"] not in ("", None):
            return True
        return False

    @staticmethod
    def validate_edit_category_request(new_categories_request: request) -> bool:
        if "id" in new_categories_request and \
                "name" in new_categories_request and \
                "description" in new_categories_request and \
                new_categories_request["id"] not in ("", None) and \
                new_categories_request["name"] not in ("", None) and \
                new_categories_request["description"] not in ("", None):
            return True
        return False

    @staticmethod
    def validate_new_categories_request(new_categories_request: request) -> bool:
        if "name" in new_categories_request and \
                "description" in new_categories_request and \
                new_categories_request["name"] not in ("", None) and \
                new_categories_request["description"] not in ("", None):
            return True
        return False

    @staticmethod
    def get_all_categories() -> List[dict]:
        categories = [dict(id=category.id, name=category.name, description=category.description)
                      for category in AppDB.db_session.query(Category).filter(
                Category.business_id == session["business_id"]
        ).all()]

        return categories

    @staticmethod
    def get_category_within_business(category_id: int) -> Category:
        return AppDB.db_session.query(Category).filter(
            Category.id == category_id,
            Category.business_id == session["business_id"]
        ).first()


# Create category view
category_view = CategoryAPI.as_view("category")

# Create category blueprint
category_bp = Blueprint(
    name="category_bp",
    import_name=__name__,
    url_prefix="/category"
)

# Create category endpoint URLs
category_bp.add_url_rule(rule="", view_func=category_view)
