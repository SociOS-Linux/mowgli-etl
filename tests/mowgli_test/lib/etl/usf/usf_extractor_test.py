from mowgli.lib.etl.usf.usf_constants import STRENGTH_FILE_KEY
from mowgli.lib.etl.usf.usf_extractor import USFExtractor


def test_usf_extractor(pipeline_storage, strengths, url):
    extractor = USFExtractor()
    extraction = extractor.extract(force=False, storage=pipeline_storage, url=url, target="usf_test_data.xml")
    with open(extraction[STRENGTH_FILE_KEY], mode='r') as strength_file:
        contents = strength_file.read()
        expected_contents = strengths.read()
        assert contents == expected_contents