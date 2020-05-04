from pathlib import Path
from typing import Dict, Tuple

from mowgli.lib.etl._extractor import _Extractor
from mowgli.lib.etl._pipeline import _Pipeline
from mowgli.lib.etl.mapper.mappers import Mappers
from mowgli.lib.etl.pipeline_storage import PipelineStorage
from mowgli.lib.etl.pipeline_wrapper import PipelineWrapper


class CombinedPipelineExtractor(_Extractor):
    """
    Extracts the CSKG formatted result of one or more pipelines
    """

    def __init__(self, *, pipelines: Tuple[_Pipeline, ...]):
        super().__init__()
        self.__pipelines = pipelines

    def extract(self, *, force: bool = False, storage: PipelineStorage) -> Dict[str, Tuple[Path, ...]]:
        self._logger.info("Starting combined extraction")
        node_file_paths, edge_file_paths = [], []

        with Mappers() as mappers:
            for pipeline in self.__pipelines:
                storage = PipelineStorage(pipeline_id=pipeline.id, root_data_dir_path=storage.root_data_dir_path)
                pipeline_wrapper = PipelineWrapper(pipeline, storage)

                pipeline_wrapper.extract_transform_load(force=force)

                node_file_path = storage.loaded_data_dir_path / 'nodes.csv'
                edge_file_path = storage.loaded_data_dir_path / 'edges.csv'
                node_file_paths.append(node_file_path)
                edge_file_paths.append(edge_file_path)
        self._logger.info("Finished combined extraction")
        return {
            'nodes_csv_file_paths': tuple(node_file_paths),
            'edges_csv_file_paths': tuple(edge_file_paths)
        }