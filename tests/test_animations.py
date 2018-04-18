import pytest

from highlight.animations import linear_transition


class TestLinearTransition(object):
    def test_less_than_two_steps(self):
        start = (1, 2, 4)
        end = (9, 10, 12)

        with pytest.raises(ValueError):
            next(linear_transition(start, end, 0))

    def test_steps(self):
        start = (1, 2, 4)
        end = (9, 10, 12)

        res = list(linear_transition(start, end, 4))
        expected = [
            [3, 4, 6],
            [5, 6, 8],
            [7, 8, 10],
            [9, 10, 12]
        ]

        assert all(y == pytest.approx(x) for x, y in zip(res, expected))
