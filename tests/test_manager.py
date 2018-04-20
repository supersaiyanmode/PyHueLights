from highlight.manager import construct_body

from utils import CustomResourceTestBase


class TestDictParser(CustomResourceTestBase):
    pass


class TestConstructBody(CustomResourceTestBase):
    def test_construct_body(self):
        resource = self.get_resource(self.obj)

        resource.field3.sub2.test = 5

        res = construct_body(resource)
        expected = {
            "field3": {
                "sub2": {"test": 5}
            }
        }

        assert res == expected

    def test_construct_body_none(self):
        assert construct_body(None) is None
