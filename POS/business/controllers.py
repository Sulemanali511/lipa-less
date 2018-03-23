from flask import Blueprint, render_template, request, logging
from flask_login import login_required, current_user

from ..constants import APP_NAME, OWNER_ROLE_NAME

from ..base.app_view import AppView

from ..models.base_model import AppDB
from ..models.business import Business
from ..models.role import Role
from ..models.user_business import UserBusiness


class BusinessAPI(AppView):
    @staticmethod
    @login_required
    def get():
        """
            Gets and returns a page filled with a list of all businesses
            associated with the current user
        :return:
        """
        return render_template(
            template_name_or_list="business.html",
            title="%s: %s" % (APP_NAME, "business")
        )

    @staticmethod
    @login_required
    def post():
        """
            Adds a new business
        :return:
        """
        business_request = request.get_json()

        if not business_request:
            error = "Request mime type for JSON not specified"
            logging.getLogger().log(
                logging.ERROR,
                error
            )
            return BusinessAPI.send_response(
                msg=error,
                status=400
            )

        if not BusinessAPI.request_is_filled(business_request):
            return BusinessAPI.send_response(
                msg="Fill in all details",
                status=400
            )
        if BusinessAPI.business_exists(business_request["business_name"]):
            return BusinessAPI.send_response(
                msg="Business by that name exists",
                status=409
            )

        # Business info
        business_name = business_request["business_name"]
        contact_number = business_request["contact_number"]

        # Create business data object
        business = Business(
            name=business_name,
            contact_no=contact_number,
        )

        # Assign owner role to user
        # First find the owner role object
        owner_role = AppDB.db_session.query(Role).filter(
            Role.name == OWNER_ROLE_NAME
        ).first()

        # Owner role exists so associate currently logged in user to it
        # but relative to the business
        user_business = UserBusiness(owner_role.id)
        user_business.business = business
        user_business.user = current_user

        # Add business info to database
        AppDB.db_session.add(business)
        # Add user role info to database
        AppDB.db_session.add(user_business)

        AppDB.db_session.commit()

        return BusinessAPI.send_response(
            msg="Business created",
            status=200
        )

    @staticmethod
    def request_is_filled(client_request):
        """
        Checks to confirm that the necessary fields exist and are filled
        :param client_request: The JSON request
        :return: True if exists and are filled, False otherwise
        """
        return ("business_name" in client_request.keys() and
                "contact_number" in client_request.keys()) and \
               (client_request["business_name"] not in ["", None]) and \
               (client_request["contact_number"] not in ["", None])

    @staticmethod
    def business_exists(name):
        """
            Checks if the business already exists
        :param name: Business name
        :return: True if they have an account, False otherwise
        """
        if AppDB.db_session.query(Business).filter(
                Business.name == name
        ).first():
            return True
        return False


# Create business view
business_view = BusinessAPI.as_view("business")

# Create business blueprint
business_bp = Blueprint(
    name="business_bp",
    import_name=__name__,
    url_prefix="/business",
    static_folder="static",
    template_folder="templates"
)

# Create endpoints
business_bp.add_url_rule(
    rule="",
    view_func=business_view
)
