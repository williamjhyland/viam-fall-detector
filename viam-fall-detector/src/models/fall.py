import sys
from typing import ClassVar, Final, List, Mapping, Optional, Sequence

from typing_extensions import Self
from viam.media.video import ViamImage
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import PointCloudObject, ResourceName
from viam.proto.service.vision import Classification, Detection, GetPropertiesResponse
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.services.vision import Vision, CaptureAllResult
from viam.utils import ValueTypes, struct_to_dict, from_dm_from_extra
from viam.components.camera import Camera
from viam.errors import NoCaptureToStoreError
from typing import cast

class Fall(Vision, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("bill", "viam-fall-detector"), "fall")

    def __init__(self, name: str):
        super().__init__(name)

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        vision = cls(config.name)
        vision.reconfigure(config, dependencies)
        return vision

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        self.config = config
        self.DEPS = dependencies
        config_dict = struct_to_dict(config.attributes)
        self.base_vision_name = config_dict["base_vision_name"]
        self.valid_labels = config_dict["valid_labels"]
        self.label_confidence = config_dict["label_confidence"]
        self.camera_name = config_dict["camera_name"]

    async def get_detections_from_camera(self, camera_name: str, *, extra=None, timeout=None) -> List[Detection]:
        vision = cast(Vision, self.DEPS[Vision.get_resource_name(self.base_vision_name)])
        detections = await vision.get_detections_from_camera(camera_name)
        return [d for d in detections if d.class_name in self.valid_labels]

    async def get_detections(self, image: ViamImage, *, extra=None, timeout=None) -> List[Detection]:
        vision = cast(Vision, self.DEPS[Vision.get_resource_name(self.base_vision_name)])
        detections = await vision.get_detections(image)
        return [d for d in detections if d.class_name in self.valid_labels]

    async def get_classifications_from_camera(self, camera_name: str, count: int, *, extra=None, timeout=None) -> List[Classification]:
        detections = await self.get_detections_from_camera(camera_name)
        return self._classify_detections(detections)

    async def get_classifications(self, image: ViamImage, count: int, *, extra=None, timeout=None) -> List[Classification]:
        detections = await self.get_detections(image)
        return self._classify_detections(detections)

    def _classify_detections(self, detections: List[Detection]) -> List[Classification]:
        classifications = []
        for d in detections:
            if d.class_name in self.valid_labels and d.confidence >= self.label_confidence:
                height = d.y_max - d.y_min
                width = d.x_max - d.x_min
                classification = Classification(
                    class_name="No fall" if height > width else "Fall",
                    confidence=d.confidence
                )
                classifications.append(classification)
        return classifications

    async def capture_all_from_camera(
        self,
        camera_name: Optional[str] = None,
        return_image: bool = False,
        return_classifications: bool = False,
        return_detections: bool = False,
        return_object_point_clouds: bool = False,
        *,
        extra: Optional[Mapping[str, ValueTypes]] = None,
        timeout: Optional[float] = None
    ) -> CaptureAllResult:
        result = CaptureAllResult()
        camera = cast(Camera, self.DEPS[Camera.get_resource_name(camera_name or self.camera_name)])
        result.image = await camera.get_image(mime_type="image/jpeg")
        result.detections = await self.get_detections(result.image)
        result.classifications = await self.get_classifications(result.image, 1)

        if from_dm_from_extra(extra):
            if not any(c.class_name == "Fall" for c in result.classifications):
                raise NoCaptureToStoreError

        return result

    async def get_object_point_clouds(self, camera_name: str, *, extra=None, timeout=None) -> List[PointCloudObject]:
        return []

    async def get_properties(self, *, extra=None, timeout=None) -> GetPropertiesResponse:
        return GetPropertiesResponse(
            classifications_supported=True,
            detections_supported=True,
            object_point_clouds_supported=False
        )

    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout=None, **kwargs) -> Mapping[str, ValueTypes]:
        return {}
