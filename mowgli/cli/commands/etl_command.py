import logging
import os.path
from importlib import import_module
from inspect import isclass
from typing import Type

from configargparse import ArgParser

from mowgli import paths
from mowgli.cli.commands._command import _Command
from mowgli.lib.etl._pipeline import _Pipeline
from mowgli.lib.etl.pipeline_storage import PipelineStorage
from mowgli.lib.etl.pipeline_wrapper import PipelineWrapper


class EtlCommand(_Command):
    def add_arguments(self, arg_parser: ArgParser):
        arg_parser.add_argument(
            "--data-dir-path",
            help="path to a directory to store extracted and transformed data",
        )
        arg_parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="force extract and transform, ignoring any cached data",
        )
        arg_parser.add_argument(
            "--force-extract",
            action="store_true",
            help="force extract, ignoring any cached data",
        )
        arg_parser.add_argument(
            "--force-transform",
            action="store_true",
            help="force transform, ignoring any cached data",
        )
        arg_parser.add_argument(
            "--fuseki-data-url", default="http://fuseki:3030/ds/data"
        )
        arg_parser.add_argument(
            "--pipeline-module", help="module name for the pipeline implementation"
        )

    def __call__(self, args, arg_parser):
        pipeline_class = self.__import_pipeline_class(args)
        pipeline_class.add_arguments(arg_parser)

        args = arg_parser.parse_args()

        pipeline = self.__instantiate_pipeline(args, pipeline_class)
        pipeline_storage = PipelineStorage(
            pipeline_id=pipeline.id,
            root_data_dir_path=self.__create_data_dir_path(args),
        )
        pipeline_wrapper = PipelineWrapper(pipeline=pipeline, storage=pipeline_storage)

        force = bool(getattr(args, "force", False))
        force_extract = force or bool(getattr(args, "force_extract", False))
        force_transform = force or bool(getattr(args, "force_transform", False))

        extract_kwds = pipeline_wrapper.extract(force=force_extract)
        graph_generator = pipeline_wrapper.transform(
            force=force_transform, **extract_kwds
        )
        pipeline_wrapper.load(graph_generator)

    def __create_data_dir_path(self, args) -> str:
        data_dir_path = args.data_dir_path
        if data_dir_path is None:
            for data_dir_path in (
                # In the container
                "/data",
                # In the checkout
                paths.DATA_DIR,
            ):
                if os.path.isdir(data_dir_path):
                    break
        if not os.path.isdir(data_dir_path):
            raise ValueError("data dir path %s does not exist" % data_dir_path)
        if not os.path.isdir(data_dir_path):
            os.makedirs(data_dir_path)
            self._logger.info("created pipeline data directory %s", data_dir_path)
        return data_dir_path

    def __import_pipeline_class(self, args) -> Type[_Pipeline]:
        try_pipeline_module_names = [args.pipeline_module]
        if not "." in args.pipeline_module:
            try_pipeline_module_names.append(
                ".%s.%s" % (args.pipeline_module, args.pipeline_module + "_pipeline")
            )

        first_import_error = None
        pipeline_module = None
        for pipeline_module_name_i, pipeline_module_name in enumerate(
            try_pipeline_module_names
        ):
            try:
                pipeline_module = import_module(
                    pipeline_module_name, _Pipeline.__module__.rsplit(".", 1)[0]
                )
                break
            except ImportError as e:
                if pipeline_module_name_i == 0:
                    first_import_error = e

        if pipeline_module is None:
            raise first_import_error

        for attr in dir(pipeline_module):
            value = getattr(pipeline_module, attr)
            if isclass(value) and issubclass(value, _Pipeline):
                return value
        raise ImportError("no Pipeline in the %s module" % pipeline_module.__name__)

    def __instantiate_pipeline(self, args, pipeline_class, **kwds) -> _Pipeline:
        pipeline_kwds = vars(args).copy()
        pipeline_kwds.pop("c")
        pipeline_kwds.pop("data_dir_path")
        pipeline_kwds.pop("force")
        pipeline_kwds.pop("force_extract")
        pipeline_kwds.pop("force_transform")
        pipeline_kwds.pop("logging_level")
        pipeline_kwds.pop("pipeline_module")
        pipeline_kwds.update(kwds)
        return pipeline_class(**pipeline_kwds)