from firebase_functions.utils import PathPattern


def test_path_segmentation():
    """
    Testing if a path is being segmented correctly.
    """
    path = PathPattern("/foo/bar")
    assert path.segments[0].name == "segment"
    assert path.segments[1].name == "segment"

    path = PathPattern("/foo/bar/{baz}")
    assert path.segments[0].name == "segment"
    assert path.segments[1].name == "segment"
    assert path.segments[2].name == "single-capture"

    path = PathPattern("/foo/bar/**")
    assert path.segments[0].name == "segment"
    assert path.segments[1].name == "segment"
    assert path.segments[2].name == "segment"
    assert path.segments[2].is_multi_segment_wildcard()

    path = PathPattern("/foo/bar/*")
    assert path.segments[0].name == "segment"
    assert path.segments[1].name == "segment"
    assert path.segments[2].is_single_segment_wildcard()

    path = PathPattern("/foo/bar/{baz=**}")
    assert path.segments[2].name == "multi-capture"

    path = PathPattern("/foo/bar/{baz=*}")
    assert path.segments[2].name == "single-capture"

    path = PathPattern("/foo/bar/{baz=**}/foo/bar/{baz=*}")
    assert path.segments[2].is_multi_segment_wildcard()
    assert path.segments[5].is_single_segment_wildcard()


def test_path_extract_matches():
    """
    Test if matches are extracted correctly in a path
    """

    path = PathPattern("/foo/bar/{baz=**}")
    assert path.extract_matches("/foo/bar/123") == {"baz": "123"}
