from mowgli.lib.etl.food_on.food_on_pipeline import FoodOnPipeline
from mowgli.lib.etl.pipeline_wrapper import PipelineWrapper


def test_food_on_pipeline(pipeline_storage):
    pipeline = FoodOnPipeline()
    pipeline_wrapper = PipelineWrapper(pipeline, pipeline_storage)

    pipeline_wrapper.extract_transform_load(force=False)