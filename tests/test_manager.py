from highlight.manager import construct_body

from utils import CustomResourceTestBase

class TestConstructBody(CustomResourceTestBase):
    def test_construct_body(self):
        resource = self.get_resource(self.obj)

        resource.field2 = "new_value"
        resource.field3.sub2.test = 5

        res = construct_body(resource)
        expected = {
            "f2": "new_value",
            "field3": {
                "sub2": {"test": 5}
            }
        }

        assert res == expected
