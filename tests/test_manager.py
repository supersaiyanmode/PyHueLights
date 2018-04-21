from highlight.manager import construct_body, dict_parser

from utils import CustomResourceTestBase, CustomResource


class TestDictParser(CustomResourceTestBase):
    def test_parse(self):
        parser = dict_parser(CustomResource)
        res = parser({"1": self.obj})
        assert isinstance(res["1"], CustomResource)
        assert res["1"].id == "1"
        assert res["1"].field1 == "blah"


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
