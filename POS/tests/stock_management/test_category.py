from POS.tests.base.base_test_case import BaseTestCase

from POS.models.base_model import AppDB
from POS.models.stock_management.category import Category


class TestCategory(BaseTestCase):
    def setUp(self):
        self.init_test_app()
        self.create_users()

    def test_get_categories(self):
        # Login as cashier
        self.login(
            self.cashier_email,
            self.cashier_password,
        )

        # Select business
        self.select_business(self.business_id)

        # Get categories
        rv = self.test_app.get("/category")

        self.assertIn(b"200", rv.data)

    def test_add_category(self):
        # Login as an admin
        self.login_as_admin()

        # Category info
        name = "test_category"
        description = "Just a test_category"

        self.send_json_post(
            endpoint="/category",
            name=name,
            description=description
        )

        # Check if category has been added
        self.assertEqual(AppDB.db_session.query(Category).count(), 1)

    def test_edit_category(self):
        # Login as an admin
        self.login_as_admin()

        # Add category
        self.add_category()

        # Edit category
        category = AppDB.db_session.query(Category).first()

        new_category_name = self.category_name + "more stuff"
        new_category_description = self.category_description + "more stuff"

        self.send_json_put(
            endpoint="/category",
            id=str(category.id),
            name=new_category_name,
            description=new_category_description
        )

        # Check if new info was saved
        category = AppDB.db_session.query(Category).first()

        self.assertEqual(new_category_name.strip().lower(), category.name)
        self.assertEqual(new_category_description.strip().lower(), category.description)

    def test_remove_category(self):
        # Login as admin
        self.login_as_admin()

        # Add a category
        self.add_category()

        # Get the category
        category = AppDB.db_session.query(Category).first()

        # Delete category
        self.send_json_delete(
            endpoint="/category",
            id=str(category.id)
        )

        # Check if category was removed
        self.assertEqual(AppDB.db_session.query(Category).count(), 0)

    def login_as_admin(self):
        # Login as an admin
        self.login(
            email=self.admin_email,
            password=self.admin_password
        )

        # Select business
        self.select_business(self.business_id)

    def add_category(self):
        # Category info
        self.category_name = "test_category"
        self.category_description = "Just a test_category"

        return self.send_json_post(
            endpoint="/category",
            name=self.category_name,
            description=self.category_description
        )
